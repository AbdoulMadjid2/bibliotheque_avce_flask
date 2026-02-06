from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from functools import wraps
from werkzeug.security import check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from bson import ObjectId
from flask import jsonify
from flask import render_template

app = Flask(__name__)
app.secret_key = "cle_secrete_bibliotheque_2026"

client = MongoClient("mongodb://localhost:27017/")
db = client["bibliotheque"]
auteurs = db["auteurs"]
categories = db["categories"]
adherents = db["adherents"]
livres = db["livres"]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form["login"]
        password = request.form["password"]

        user = db.users.find_one({"login": login})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]
            session["login"] = user["login"]

            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Identifiants incorrects")

    return render_template("login.html")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def dashboard():
    nb_livres = db.livres.count_documents({})
    nb_auteurs = db.auteurs.count_documents({})
    nb_adherents = db.adherents.count_documents({})

    nb_emprunts_en_cours = db.emprunts.count_documents({
        "statut": {"$ne": "Retourné"}
    })
    

    return render_template(
        "admin_dashboard.html",
        nb_livres=nb_livres,
        nb_auteurs=nb_auteurs,
        nb_emprunts_en_cours=nb_emprunts_en_cours,
        nb_adherents=nb_adherents 
    )

@app.route("/auteurs")
@login_required
def liste_auteurs():
    data = auteurs.find()
    return render_template("auteurs/index.html", auteurs=data)
@app.route("/auteurs/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_auteur():
    if request.method == "POST":
        auteurs.insert_one({
            "nom": request.form.get("nom"),
            "prenom": request.form.get("prenom"),
            "nationalite": request.form.get("nationalite"),
            "date_naissance": request.form.get("date_naissance")
        })
        return jsonify(success=True)

    return render_template("auteurs/ajouter.html")

@app.route("/auteurs/modifier/<id>", methods=["GET", "POST"])
@login_required
def modifier_auteur(id):
    auteur = db.auteurs.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        db.auteurs.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "nom": request.form.get("nom"),
                "prenom": request.form.get("prenom"),
                "nationalite": request.form.get("nationalite"),
                "date_naissance": request.form.get("date_naissance")
            }}
        )
        return jsonify(success=True)

    return render_template("auteurs/modifier.html", auteur=auteur)

@app.route("/auteurs/supprimer/<id>", methods=["POST"])
@login_required
def supprimer_auteur(id):
    db.auteurs.delete_one({"_id": ObjectId(id)})
    return jsonify(success=True)

@app.route("/categories")
@login_required
def liste_categories():
    data = categories.find()
    return render_template("categories/index.html", categories=data)
@app.route("/categories/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_categorie():
    if request.method == "POST":
        categories.insert_one({
            "libelle": request.form["libelle"],
        })
        return jsonify(success=True)
    return render_template("categories/ajouter.html")

@app.route("/categories/modifier/<id>", methods=["GET", "POST"])
@login_required
def modifier_categorie(id):
    categorie = db.categories.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        db.categories.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "libelle": request.form["libelle"]
            }}
        )
        return jsonify(success=True)

    return render_template("categories/modifier.html", categorie=categorie)
@app.route("/categories/supprimer/<id>")
@login_required
def supprimer_categorie(id):
    db.categories.delete_one({"_id": ObjectId(id)})
    return jsonify(success=True)

@app.route("/adherents")
@login_required
def liste_adherents():
    data = adherents.find()
    return render_template("adherents/index.html", adherents=data)
@app.route("/adherents/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_adherent():
    if request.method == "POST":
        adherents.insert_one({
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "email": request.form["email"],
            "telephone": request.form["telephone"],
            "adresse": request.form["adresse"]
        })
        return jsonify(success=True)
    return render_template("adherents/ajouter.html")

@app.route("/adherents/modifier/<id>", methods=["GET", "POST"])
@login_required
def modifier_adherent(id):
    adherent = db.adherents.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        result = db.adherents.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "nom": request.form.get("nom"),
                "prenom": request.form.get("prenom"),
                "email": request.form.get("email"),
                "telephone": request.form.get("telephone"),
                "adresse": request.form.get("adresse")
            }}
        )

        return jsonify(success=result.modified_count == 1)

    return render_template("adherents/modifier.html", adherent=adherent)


@app.route("/adherents/supprimer/<id>", methods=["POST"])
@login_required
def supprimer_adherent(id):
    result = db.adherents.delete_one({"_id": ObjectId(id)})
    return jsonify(success=result.deleted_count == 1)


@app.route("/livres")
@login_required
def liste_livres():
    livres = livres = list(db.livres.aggregate([
        {
            "$lookup": {
                "from": "categories",
                "localField": "categorie_id",
                "foreignField": "_id",
                "as": "categorie"
            }
        },
        {
            "$lookup": {
                "from": "auteurs",
                "localField": "auteurs",
                "foreignField": "_id",
                "as": "auteurs_details"
            }
        }
    ]))

    return render_template("livres/index.html", livres=livres)


@app.route("/livres/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_livre():
    categories = db.categories.find()
    auteurs = db.auteurs.find()

    if request.method == "POST":
        db.livres.insert_one({
            "titre": request.form["titre"],
            "annee": request.form.get("annee"),
            "nbExemplaires": int(request.form.get("nbExemplaires", 1)),
            "categorie_id": ObjectId(request.form["idCategorie"]),
            "auteurs": [ObjectId(request.form["auteurs"])]
        })
        return jsonify(success=True)

    return render_template("livres/ajouter.html", categories=categories, auteurs=auteurs )

@app.route("/livres/modifier/<id>", methods=["GET", "POST"])
@login_required
def modifier_livre(id):
    livre = db.livres.find_one({"_id": ObjectId(id)})
    categories = list(db.categories.find())
    auteurs = list(db.auteurs.find())

    if request.method == "POST":
        update_data = {
            "titre": request.form.get("titre"),
            "annee": request.form.get("annee"),
            "nbExemplaires": int(request.form.get("nbExemplaires", 1))
        }

        if request.form.get("idCategorie"):
            update_data["categorie_id"] = ObjectId(request.form["idCategorie"])
        else:
            update_data["categorie_id"] = None

        if request.form.get("auteur_id"):
            update_data["auteurs"] = [ObjectId(request.form["auteur_id"])]

        result = db.livres.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        return jsonify(success=result.modified_count == 1)

    return render_template("livres/modifier.html", livre=livre, categories=categories, auteurs=auteurs)
@app.route("/livres/supprimer/<id>", methods=["POST"])
@login_required
def supprimer_livre(id):
    result = db.livres.delete_one({"_id": ObjectId(id)})
    return jsonify(success=result.deleted_count == 1)
from datetime import date

@app.route("/emprunts")
@login_required
def liste_emprunts():
    today = date.today()

    emprunts = list(db.emprunts.find())

    for e in emprunts:
        e["adherent"] = db.adherents.find_one({"_id": e["adherent_id"]})
        e["livre"] = db.livres.find_one({"_id": e["livre_id"]})

        if e["date_retour_reelle"] is None:
            date_prevue = date.fromisoformat(e["date_retour_prevue"])
            if today > date_prevue:
                e["statut_affiche"] = "En retard"
            else:
                e["statut_affiche"] = "En cours"
        else:
            e["statut_affiche"] = "Retourné"

    return render_template("emprunts/index.html", emprunts=emprunts)



@app.route("/emprunts/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_emprunt():
    adherents = list(db.adherents.find())
    livres = list(db.livres.find())

    if request.method == "POST":
        db.emprunts.insert_one({
            "adherent_id": ObjectId(request.form["idAdherent"]),
            "livre_id": ObjectId(request.form["idLivre"]),
            "date_emprunt": date.today().isoformat(),
            "date_retour_prevue": request.form["dateRetourPrevue"],
            "date_retour_reelle": None,
            "statut": "En cours"
        })
        return jsonify(success=True)
    return render_template("emprunts/ajouter.html", adherents=adherents,livres=livres )
@app.route("/emprunts/retourner/<id>", methods=["POST"])
@login_required
def retourner_livre(id):
    today = date.today().isoformat()

    result = db.emprunts.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "date_retour_reelle": today,
            "statut": "Retourné"
        }}
    )

    return jsonify(success=result.modified_count == 1)


if __name__ == "__main__":
    app.run(debug=True)
