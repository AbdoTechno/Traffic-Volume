# Before Push Checklist

## 1. Local environment
- Confirm the project runs locally.
- Confirm the virtual environment is active.
- Confirm dependencies are installed from requirements.txt.
- Confirm .env exists locally with the real WeatherAPI key.
- Confirm .env is excluded from Git by .gitignore.

## 2. Project files review
- README.md is final and clear.
- .env.example contains the public template only.
- requirements.txt includes all runtime dependencies.
- Procfile exists for Railway.
- railway.json exists for deployment configuration.
- runtime.txt exists for the Python version.
- app/main.py exposes the app entrypoint correctly.

## 3. API verification
- Confirm the local app responds at /.
- Confirm the POST /predict endpoint returns JSON forecast data.
- Confirm the weather request is using WeatherAPI.
- Confirm the app handles city and date input correctly.

## 4. Git hygiene
- Check current branch status.
- Ensure no real secrets are in tracked files.
- Ensure .env is not staged.
- Ensure .env.example is tracked.
- Review the diff before staging.

## 5. Suggested staged commit sequence
Use small progressively meaningful commits:

1. Commit: project setup and repo structure
   - README, .gitignore, requirements, folders
2. Commit: modeling pipeline
   - notebook updates, preprocessing, artifact export
3. Commit: production prediction backend
   - predictor, feature builder, weather client, API routes
4. Commit: front-end polish
   - HTML, CSS, JavaScript, UI improvements
5. Commit: deployment config
   - Procfile, railway.json, runtime.txt, deploy checklist
6. Commit: final handoff cleanup
   - README final touch, env template, final verification notes

## 6. Railway readiness
- GitHub repository is public or connected to Railway.
- The project is pushed.
- Railway is connected to the repo.
- WEATHER_API_KEY is added in Railway variables.
- The app port uses the environment variable PORT automatically.
- A successful deployment check is done through the root and predict endpoints.

## 7. Final check before push
- README is up to date.
- no accidental .env in repo
- no secret keys in code or commit history
- app launches with uvicorn
- API forecast works locally
- GitHub and Railway are ready for the next step
