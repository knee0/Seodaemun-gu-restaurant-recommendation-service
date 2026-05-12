# Basic GitHub commands

### 수집한 데이터는 공유하지 말아주세요!
합법적으로 수집한 것이 아니라서, 나중에 레포를 public으로 전환하는데 차질이 생겨요.

#### Removed problematic commit on 5/12. Just now, before working:
```
git fetch origin
git reset --hard origin/main
```

#### Before working
```
git checkout main
git pull --rebase
git checkout -b branch-name
```

#### Update work
```
git add .
git commit -m "commit message"
git push -u origin branch-name
```

#### After merge & branch delete (via GitHub)
```
git checkout main
git pull --rebase
git branch -d branch-name
git fetch --prune
```
