# 식당 대표 이미지 준비

식당 데이터에 `thumbnail_url` 또는 `image_url`이 있으면 카드와 상세 페이지에서 대표 이미지로 보여줍니다.

네이버 플레이스 공유 썸네일을 사용하려면 식당 데이터에 `naver_place_id` 또는 `naver_map_url`을 넣은 뒤 아래 명령을 실행하세요.

```bash
npm run fetch:thumbnails
```

기본 입력/출력 파일은 `public/data/web_mock_restaurants.json`입니다. 다른 파일을 쓰려면 아래처럼 지정할 수 있습니다.

```bash
node scripts/fetch-naver-thumbnails.mjs --input public/data/web_mock_restaurants.json --output public/data/web_mock_restaurants.json
```

# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
