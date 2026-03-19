from flask import Flask, render_template, request, redirect, session
from models import db, User, RoadmapProgress
from data_store import domains

app = Flask(__name__)

app.secret_key = "skillgapsecret"

# Railway MySQL connection
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:BYXrPiTKlaotvlnfGtBeNyVxpBstwXhp@interchange.proxy.rlwy.net:30916/railway"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,   # 🔥 VERY IMPORTANT (auto reconnect)
    "pool_recycle": 280,     # reconnect before timeout
}

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------- LOGIN PAGE ----------------

@app.route("/")
def home():
    return render_template("login.html")


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # check if user already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template(
                "signup.html",
                error="User already exists"
            )

        new_user = User(username=username, password=password)

        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    return render_template("signup.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    user = User.query.filter_by(
        username=username,
        password=password
    ).first()

    if user:

        session["user"] = username

        return redirect("/analysis")

    return redirect("/")


# ---------------- ANALYSIS PAGE ----------------

@app.route("/analysis")
def analysis():

    if "user" not in session:
        return redirect("/")

    return render_template("analysis.html", domains=domains)


# ---------------- ANALYZE SKILLS ----------------

@app.route("/analyze", methods=["POST","GET"])
def analyze():

    if "user" not in session:
        return redirect("/")

    # If returning from roadmap
    if request.method == "GET" and "analysis_result" in session:

        result = session["analysis_result"]

        return render_template(
            "result.html",
            domain=result["domain"],
            domain_data=domains[result["domain"]],
            user_skills=result["user_skills"],
            missing_skills=result["missing_skills"]
        )

    # Normal analysis
    domain = request.form["domain"]

    user_skills = request.form["skills"].lower().split(",")

    user_skills = [s.strip() for s in user_skills]

    domain_data = domains[domain]

    required_skills = [s.lower() for s in domain_data["skills"]]

    user_skill_set = set(user_skills)

    missing_skills = [s for s in required_skills if s not in user_skill_set]

    # store result so roadmap can return
    session["analysis_result"] = {
        "domain": domain,
        "user_skills": user_skills,
        "missing_skills": missing_skills
    }

    return render_template(
        "result.html",
        domain=domain,
        domain_data=domain_data,
        user_skills=user_skills,
        missing_skills=missing_skills
    )


# ---------------- MY PROGRESS ----------------

@app.route("/progress")
def progress():

    if "user" not in session:
        return redirect("/")

    all_progress = RoadmapProgress.query.filter_by(username=session["user"]).all()

    # group by domain
    domain_map = {}
    for p in all_progress:
        if p.domain not in domain_map:
            domain_map[p.domain] = []
        domain_map[p.domain].append(p)

    progress_data = []
    for domain_name, records in domain_map.items():
        if domain_name not in domains:
            continue
        steps = domains[domain_name]["roadmap"]
        completed_steps = [r.step for r in records if r.completed]
        total = len(steps)
        completed = len([s for s in steps if s in completed_steps])
        pct = int((completed / total) * 100) if total > 0 else 0
        step_list = [{"name": s, "completed": s in completed_steps} for s in steps]
        progress_data.append({
            "domain": domain_name,
            "steps": step_list,
            "total": total,
            "completed": completed,
            "pct": pct
        })

    return render_template("progress.html", progress_data=progress_data)


# ---------------- ROADMAP ----------------

@app.route("/roadmap/<domain>")
def roadmap(domain):

    if "user" not in session:
        return redirect("/")

    if domain not in domains:
        return "Domain not found"

    steps = domains[domain]["roadmap"]

    progress = RoadmapProgress.query.filter_by(
        username=session["user"],
        domain=domain
    ).all()

    completed_steps = [p.step for p in progress if p.completed]

    return render_template(
        "roadmap.html",
        domain=domain,
        steps=steps,
        completed_steps=completed_steps
    )


# ---------------- UPDATE PROGRESS ----------------

@app.route("/update_progress", methods=["POST"])
def update_progress():

    if "user" not in session:
        return redirect("/")

    step = request.form["step"]
    domain = request.form["domain"]

    record = RoadmapProgress.query.filter_by(
        username=session["user"],
        domain=domain,
        step=step
    ).first()

    if record:

        record.completed = not record.completed

    else:

        record = RoadmapProgress(
            username=session["user"],
            domain=domain,
            step=step,
            completed=True
        )

        db.session.add(record)

    db.session.commit()

    return redirect(f"/roadmap/{domain}")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
