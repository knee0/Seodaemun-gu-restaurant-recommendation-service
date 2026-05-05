# Basic GitHub commands ദ്ദി(◝ ⩊ ◜)

#### Setup
git clone https://github.com/eastYonsei/test-mining-project.git
cd test-mining-project

#### Before working
git checkout main
git pull --rebase
git checkout -b branch-name

#### Update work
git add .
git commit -m "commit message"
git push -u origin branch-name

#### After merge & branch delete (via GitHub)
git checkout main
git pull --rebase
git branch -d branch-name
git fetch --prune
