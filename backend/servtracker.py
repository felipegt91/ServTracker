import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# --- CONFIGURAÇÃO ---
app = Flask(__name__)
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "servtracker.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# --- MODELOS ---
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    contact_person = db.Column(db.String(255), nullable=True)
    projects = db.relationship(
        "Project", backref="client", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name, "contact_person": self.contact_person}


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
@app.route("/api/clients", methods=["GET"])
def get_clients():
    return jsonify([c.to_dict() for c in Client.query.order_by(Client.name).all()])


@app.route("/api/clients", methods=["POST"])
def create_client():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "O nome do cliente é obrigatório."}), 400
    if Client.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Um cliente com este nome já existe."}), 409
    new_client = Client(name=data["name"], contact_person=data.get("contact_person"))
    db.session.add(new_client)
    db.session.commit()
    return jsonify(new_client.to_dict()), 201


@app.route("/api/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    client_to_update = db.session.get(Client, client_id)
    if not client_to_update:
        return jsonify({"error": "Cliente não encontrado."}), 404
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "O nome do cliente é obrigatório."}), 400
    client_to_update.name = data["name"]
    client_to_update.contact_person = data.get(
        "contact_person", client_to_update.contact_person
    )
    db.session.commit()
    return jsonify(client_to_update.to_dict())


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


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("client_id"):
        return (
            jsonify({"error": "Nome do projeto e ID do cliente são obrigatórios."}),
            400,
        )
    if not db.session.get(Client, data["client_id"]):
        return jsonify({"error": "Cliente não encontrado."}), 404
    new_project = Project(name=data["name"], client_id=data["client_id"])
    db.session.add(new_project)
    db.session.commit()
    default_stages = [
        "Briefing",
        "Pesquisa",
        "Esboços",
        "Design Digital",
        "Revisões",
        "Finalização",
    ]
    for stage_name in default_stages:
        db.session.add(Stage(name=stage_name, project_id=new_project.id))
    db.session.commit()
    return jsonify(new_project.to_dict()), 201


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
    if Stage.query.filter_by(status="em_andamento").first():
        return jsonify({"error": "Outra etapa já está em andamento."}), 409
    stage = db.session.get(Stage, stage_id)
    if not stage:
        return jsonify({"error": "Etapa não encontrada."}), 404
    stage.status = "em_andamento"
    new_log = TimeLog(stage_id=stage.id, start_time=datetime.now(timezone.utc))
    db.session.add(new_log)
    db.session.commit()
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


@app.route("/api/stages/<int:stage_id>/complete", methods=["POST"])
def complete_stage(stage_id):
    stage = db.session.get(Stage, stage_id)
    if not stage:
        return jsonify({"error": "Etapa não encontrada."}), 404
    if stage.status == "finalizada":
        return jsonify(stage.to_dict())
    if stage.status == "em_andamento":
        log = TimeLog.query.filter_by(stage_id=stage.id, end_time=None).first()
        if log:
            log.end_time = datetime.now(timezone.utc)
            duration = log.end_time - log.start_time.replace(tzinfo=timezone.utc)
            log.duration_seconds = int(duration.total_seconds())
    stage.status = "finalizada"
    stage.end_time = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(stage.to_dict())


# --- INICIALIZAÇÃO ---
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
        c1 = Client(name="Empresa de Tecnologia X", contact_person="Ana Silva")
        c2 = Client(name="Agência de Marketing Y", contact_person="Bruno Costa")
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
