# 서대문구 맛집 추천 서비스!

### 수집한 데이터는 레포에 공유하지 말아주세요!
합법적으로 수집한 것이 아니라서, 나중에 레포를 public으로 전환하는데 차질이 생겨요.


최신 commit에 리뷰 데이터가 있어서 제외하고 다시 올렸어요. 로컬 기록이랑 꼬이지 않도록 다음 코드 실행해주세요!
```
git fetch origin
git reset --hard origin/main
```
이후로는 똑같이 'git pull --rebase' 하시면 됩니다. 해당 코드 실행하면 로컬 폴더가 웹의 최신 형태로 초기화되니, 로컬에서 수정한 사항 있으면 따로 저장해주세요!


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
