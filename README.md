# 서대문구 맛집 추천 서비스!


AI를 쓰는 것은 상관 없는데, 검수를 통해 사람이 쓴 듯한 코드를 만들어주세요. 모든 작업을 함수로 파편화해서 읽기가 너무 어렵고, 다른 스크립트의 역할을 이해하지 못한 듯 모든 일을 혼자서 다 하려고 합니다. 검수하는데 머리가 너무 아파요...


### Basic GitHub Commands

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

#### When local history differs from origin
```
git fetch origin
git reset --hard origin/main
```
