from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
source = root / "src"
dist = root / "dist"
dist.mkdir(parents=True, exist_ok=True)
for name in ("index.html", "app.js", "styles.css"):
    shutil.copy2(source / name, dist / name)
shutil.copy2(root / "review" / "cpa-financial-management-question-review.xlsx", dist / "question-review.xlsx")
print(f"Static site ready at {dist}")
