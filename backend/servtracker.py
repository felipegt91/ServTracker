import os
from datetime import datetime, timezone
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# ... (Configuração e outros modelos permanecem os mesmos) ...
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "servtracker.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    projects = db.relationship(
        "Project", backref="client", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    stages = db.relationship(
        "Stage", backref="project", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name, "client_id": self.client_id}


class Stage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="nao_iniciada", nullable=False)
    start_time = db.Column(db.DateTime(timezone=True), nullable=True)
    # NOVO CAMPO: Hora de finalização da etapa como um todo
    end_time = db.Column(db.DateTime(timezone=True), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    time_logs = db.relationship(
        "TimeLog", backref="stage", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        total_duration = sum(
            log.duration_seconds for log in self.time_logs if log.duration_seconds
        )
        active_log = next((log for log in self.time_logs if log.end_time is None), None)
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": total_duration,
            "active_log_start_time": (
                (active_log.start_time.timestamp() * 1000) if active_log else None
            ),
        }


class TimeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False)


# --- ROTAS DA API ---
# ... (Rotas GET, start e stop permanecem as mesmas) ...
@app.route("/")
def index():
    return "API do ServTracker v2 está no ar!"


@app.route("/api/clients", methods=["GET"])
def get_clients():
    return jsonify([c.to_dict() for c in Client.query.order_by(Client.name).all()])


@app.route("/api/clients/<int:client_id>/projects", methods=["GET"])
def get_projects_by_client(client_id):
    return jsonify(
        [
            p.to_dict()
            for p in Project.query.filter_by(client_id=client_id)
            .order_by(Project.name)
            .all()
        ]
    )


@app.route("/api/projects/<int:project_id>/stages", methods=["GET"])
def get_stages_by_project(project_id):
    return jsonify(
        [
            s.to_dict()
            for s in Stage.query.filter_by(project_id=project_id)
            .order_by(Stage.id)
            .all()
        ]
    )


@app.route("/api/stages/<int:stage_id>/start", methods=["POST"])
def start_stage(stage_id):
    # --- INÍCIO DOS LOGS DE DEPURAÇÃO ---
    print(f"\n--- ROTA /start ACIONADA para stage_id={stage_id} ---")

    # Vamos ver o status de TODAS as etapas ANTES de fazer qualquer coisa.
    all_stages_status = {s.id: s.status for s in Stage.query.all()}
    print("DEBUG: Estado ATUAL de todas as etapas no DB:", all_stages_status)

    # Agora fazemos a busca pela etapa ativa
    active_stage = Stage.query.filter_by(status="em_andamento").first()
    print("DEBUG: Resultado da busca por 'em_andamento':", active_stage)
    # --- FIM DOS LOGS DE DEPURAÇÃO ---

    if active_stage:
        print("!!! ERRO: Etapa ativa encontrada. Retornando 409.")
        return (
            jsonify({"error": f"A etapa '{active_stage.name}' já está em andamento."}),
            409,
        )

    stage = db.session.get(Stage, stage_id)
    if not stage:
        return jsonify({"error": "Etapa não encontrada."}), 404

    stage.status = "em_andamento"
    new_log = TimeLog(stage_id=stage.id, start_time=datetime.now(timezone.utc))
    db.session.add(new_log)
    db.session.commit()
    print(f"SUCESSO: Etapa {stage.id} alterada para 'em_andamento' e salva no DB.")
    return jsonify(stage.to_dict())


@app.route("/api/stages/<int:stage_id>/stop", methods=["POST"])
def stop_stage(stage_id):
    stage = db.session.get(Stage, stage_id)
    if not stage or stage.status != "em_andamento":
        return jsonify({"error": "Esta etapa não está em andamento."}), 400
    log = TimeLog.query.filter_by(stage_id=stage.id, end_time=None).first()
    if not log:
        return jsonify({"error": "Log de tempo ativo não encontrado."}), 400
    end_time_aware = datetime.now(timezone.utc)
    start_time_aware = log.start_time.replace(tzinfo=timezone.utc)
    duration = end_time_aware - start_time_aware
    log.end_time = end_time_aware
    log.duration_seconds = int(duration.total_seconds())
    stage.status = "pausada"
    db.session.commit()
    return jsonify(stage.to_dict())


# --- NOVA ROTA PARA FINALIZAR UMA ETAPA ---
@app.route("/api/stages/<int:stage_id>/complete", methods=["POST"])
def complete_stage(stage_id):
    stage = db.session.get(Stage, stage_id)
    if not stage:
        return jsonify({"error": "Etapa não encontrada."}), 404
    if stage.status == "finalizada":
        return jsonify(stage.to_dict())  # Já está finalizada

    # Se a etapa estiver em andamento, primeiro a paramos
    if stage.status == "em_andamento":
        log = TimeLog.query.filter_by(stage_id=stage.id, end_time=None).first()
        if log:
            log.end_time = datetime.now(timezone.utc)
            duration = log.end_time - log.start_time.replace(tzinfo=timezone.utc)
            log.duration_seconds = int(duration.total_seconds())

    # Define a etapa como finalizada
    stage.status = "finalizada"
    stage.end_time = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(stage.to_dict())


# ... (O bloco 'with app.app_context()' e 'if __name__ == '__main__'' continuam iguais) ...
with app.app_context():
    db.create_all()
    stuck_stages = Stage.query.filter_by(status="em_andamento").all()
    if stuck_stages:
        print(
            f"AVISO: Encontradas {len(stuck_stages)} etapa(s) 'presas'. Resetando status para 'pausada'."
        )
        for stage in stuck_stages:
            stage.status = "pausada"
            log_to_fix = TimeLog.query.filter_by(
                stage_id=stage.id, end_time=None
            ).first()
            if log_to_fix:
                log_to_fix.end_time = log_to_fix.start_time
                log_to_fix.duration_seconds = 0
        db.session.commit()
    if not Client.query.first():
        print("Banco de dados vazio. Populando com dados de exemplo...")
        c1 = Client(name="Empresa de Tecnologia X")
        c2 = Client(name="Agência de Marketing Y")
        db.session.add_all([c1, c2])
        db.session.commit()
        p1 = Project(name="Desenvolvimento do Novo App", client_id=c1.id)
        p2 = Project(name="Campanha de Lançamento", client_id=c2.id)
        db.session.add_all([p1, p2])
        db.session.commit()
        default_stages = [
            "Briefing",
            "Pesquisa",
            "Esboços",
            "Design Digital",
            "Revisões",
            "Finalização",
        ]
        for p in [p1, p2]:
            for name in default_stages:
                db.session.add(Stage(name=name, project_id=p.id))
        db.session.commit()
