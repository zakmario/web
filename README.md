# Gestion des rendez-vous d'un cabinet médical

Application web Django de gestion des rendez-vous d'un cabinet médical (étude de cas AU 2026-2027) :

- **Back-office** : interface d'administration Django (`/admin/`)
- **Front-office** : liste des médecins, inscription des patients, prise et suivi des rendez-vous
- **API REST** : Django REST Framework (`/api/`)

## Technologies

- Python 3.12
- Django 5.2 (LTS)
- Django REST Framework 3.18
- SQLite
- Bootstrap 5 (front-office)

## Structure

```
C:\Dja
├── env/                        # environnement virtuel (Python 3.12)
├── requirements.txt
└── GestionCabinetMedical/      # projet Django
    ├── manage.py
    ├── GestionCabinetMedical/  # settings, urls
    ├── AccountApp/             # User, Doctor, Patient, Specialty
    ├── AppointmentApp/         # Appointment
    ├── templates/              # base.html, connexion
    └── static/css/style.css
```

## Installation

```powershell
cd C:\Dja
uv venv env --python 3.12          # ou : py -3.12 -m venv env
env\Scripts\Activate.ps1
pip install -r requirements.txt

cd GestionCabinetMedical
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo         # données de démonstration (facultatif)
python manage.py runserver
```

Si PowerShell bloque l'activation : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Comptes de démonstration

Créés par `python manage.py seed_demo` (mot de passe commun : `Demo@2026`) :

| Rôle    | Nom d'utilisateur                                    |
|---------|------------------------------------------------------|
| Médecin | `dr.benali`, `dr.trabelsi`, `dr.gharbi`, `dr.mansour` |
| Patient | `patient.salah`, `patient.hamdi`                     |

## Pages

| URL                               | Description                                          |
|-----------------------------------|------------------------------------------------------|
| `/`                               | Accueil : liste des médecins (recherche, filtre par spécialité) |
| `/medecins/<id>/`                 | Profil d'un médecin                                  |
| `/comptes/inscription/`           | Création d'un compte patient                         |
| `/comptes/login/`                 | Connexion                                            |
| `/rendez-vous/`                   | Rendez-vous du patient ou consultations du médecin   |
| `/rendez-vous/nouveau/`           | Prise de rendez-vous (patient)                       |
| `/rendez-vous/<id>/confirmer/`    | Confirmation (médecin, POST)                         |
| `/rendez-vous/<id>/annuler/`      | Annulation (patient ou médecin, POST)                |
| `/rendez-vous/<id>/ordonnance/`   | Dépôt de l'ordonnance PDF (médecin)                  |
| `/admin/`                         | Back-office                                          |

## API REST

Authentification par session (API navigable) ou HTTP Basic.

| Endpoint                              | Accès                                                        |
|---------------------------------------|--------------------------------------------------------------|
| `/api/specialties/`                   | Lecture publique, écriture réservée au personnel             |
| `/api/doctors/` (`?specialty=<id>`)   | Lecture publique, écriture réservée au personnel             |
| `/api/patients/`                      | Personnel uniquement                                         |
| `/api/appointments/` (`?status=`)     | Patient : ses rendez-vous, création ; médecin : ses consultations, modification du statut et de l'ordonnance ; personnel : tout |
| `/api/appointments/<id>/confirm/`     | POST, médecin ou personnel                                   |
| `/api/appointments/<id>/cancel/`      | POST, patient, médecin ou personnel                          |

Exemple :

```powershell
curl.exe -u patient.salah:Demo@2026 http://127.0.0.1:8000/api/appointments/
```

## Règles métier

- `Doctor` et `Patient` héritent de `User` (héritage multi-tables) : `patient.pk == request.user.pk`.
- `license_number` : 6 caractères, unique ; `national_id` : 8 chiffres, unique ; `phone` : 8 chiffres.
  Ces identifiants ne sont plus modifiables après la création (admin et API).
- `birth_date` antérieure à aujourd'hui (`validate_past_date`).
- `appointment_date` postérieure à maintenant (`Appointment.clean()`), vérifiée seulement à la création
  ou si la date change : un rendez-vous passé reste modifiable (statut, ordonnance).
- Un médecin ne peut pas avoir deux rendez-vous à la même date (`UniqueConstraint`).
- Ordonnance : PDF uniquement, facultative, stockée dans `media/prescriptions/`.

## Tests

```powershell
python manage.py test
```
