import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import HomeRestaurantCard from "../components/HomeRestaurantCard";

const CATEGORY_ORDER = [
  "한식",
  "중식",
  "일식",
  "양식",
  "카페/디저트",
  "분식/간편식",
  "술집/주점",
  "아시안/세계요리"
];

const RECOMMENDATION_TABS = {
  lunch: {
    label: "점심 추천",
    title: "점심으로 이곳은 어떠세요?",
    flag: "is_lunch_recommended"
  },
  dinner: {
    label: "저녁 추천",
    title: "저녁으로 이곳은 어떠세요?",
    flag: "is_dinner_recommended"
  }
};

const normalizeCategory = (category) =>
  category === "세계요리" ? "아시안/세계요리" : category;

const pickRandomRestaurants = (items, count) => {
  const shuffled = [...items];

  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[randomIndex]] = [shuffled[randomIndex], shuffled[index]];
  }

  return shuffled.slice(0, count);
};

function HomePage() {
  const [restaurants, setRestaurants] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [recommendationMode, setRecommendationMode] = useState("lunch");
  const [recommendationShuffleKey, setRecommendationShuffleKey] = useState(0);
  const categoryRailRefs = useRef({});
  const navigate = useNavigate();

  //call restaurant data
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/web_format_scores.json`)
      .then((response) => response.json())
      .then((data) => {
        setRestaurants(data);
      })
      .catch((error) => {
        console.error("데이터를 불러오는 데 실패했습니다:", error);
      });
  }, []);

  //search bar: pass value to URL param and go to result page
  const handleSearch = () => {
    navigate(`/results?search=${encodeURIComponent(searchTerm)}`);
  };

  const getRestaurantSubtitle = (restaurant) =>
    restaurant.category_raw || restaurant.address || restaurant.category;

const getDisplayScore = (restaurant) => {
  if (restaurant.total_score === -1) {
    return "?";
  }

  return `${Math.round(restaurant.total_score * 20)}점`;
};

  const getCategoryRestaurants = (category) =>
    restaurants
      .filter((restaurant) => normalizeCategory(restaurant.category) === category)
      .sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
      .slice(0, 12);

  const scrollCategoryRail = (category, direction) => {
    const rail = categoryRailRefs.current[category];
    if (!rail) return;

    rail.scrollBy({
      left: direction * Math.round(rail.clientWidth * 0.58),
      behavior: "smooth"
    });
  };

  const handleRecommendationTabClick = (key) => {
    setRecommendationMode(key);
    setRecommendationShuffleKey((currentKey) => currentKey + 1);
  };

  const activeRecommendation = RECOMMENDATION_TABS[recommendationMode];
  const topRestaurants = useMemo(() => {
    const candidates = restaurants.filter((restaurant) => {
      if (restaurant[activeRecommendation.flag] !== true) return false;
      if (normalizeCategory(restaurant.category) === "카페/디저트") return false;

      return true;
    });

    return pickRandomRestaurants(candidates, 5);
  }, [activeRecommendation.flag, recommendationMode, recommendationShuffleKey, restaurants]);

  return (
    <div className="home-page">
      <section className="hero-section">
        <h1>당신의 취향에 맞는 맛집을 찾아보세요</h1>
        <p>5가지 평가 기준으로 맞춤 추천을 받을 수 있습니다</p>

        <div className="search-bar-wrapper">
        <input
          type="text"
          placeholder="맛집 검색..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSearch();
          }}
        />
          <button onClick={handleSearch}>맞춤 검색</button>
        </div>
      </section>

      <section className="category-recommendation-section">
        <h2 className="section-title">카테고리별 추천 맛집</h2>

        <div className="category-rail-list">
          {CATEGORY_ORDER.map((category) => {
            const categoryRestaurants = getCategoryRestaurants(category);

            if (categoryRestaurants.length === 0) {
              return null;
            }

            return (
              <section className="category-rail-section" key={category}>
                <div className="category-rail-header">
                  <h3>
                    {category}
                    <span>{categoryRestaurants.length}곳</span>
                  </h3>
                </div>

                <div className="category-rail-shell">
                  <button
                    className="rail-arrow rail-arrow-left"
                    onClick={() => scrollCategoryRail(category, -1)}
                    type="button"
                    aria-label={`${category} 추천 이전 보기`}
                  >
                    ‹
                  </button>

                  <div
                    className="category-rail"
                    ref={(element) => {
                      categoryRailRefs.current[category] = element;
                    }}
                  >
                    {categoryRestaurants.map((restaurant) => (
                      <button
                        className="category-restaurant-card"
                        key={restaurant.id}
                        onClick={() => navigate(`/restaurants/${restaurant.id}`)}
                        type="button"
                      >
                        <div className="category-restaurant-image">
                          {restaurant.thumbnail_url ? (
                            <img
                              src={restaurant.thumbnail_url}
                              alt={`${restaurant.name} 대표 이미지`}
                              loading="lazy"
                            />
                          ) : (
                            <span>{restaurant.name.slice(0, 2)}</span>
                          )}
                          <span className="category-score-badge">
                            {getDisplayScore(restaurant)}
                          </span>
                        </div>
                        <strong>{restaurant.name}</strong>
                        <span>{getRestaurantSubtitle(restaurant)}</span>
                      </button>
                    ))}
                  </div>

                  <button
                    className="rail-arrow rail-arrow-right"
                    onClick={() => scrollCategoryRail(category, 1)}
                    type="button"
                    aria-label={`${category} 추천 다음 보기`}
                  >
                    ›
                  </button>
                </div>
              </section>
            );
          })}
        </div>
      </section>

      <section className="top-section">
        <div className="section-heading-row">
          <h2 className="section-title">{activeRecommendation.title}</h2>

          <div className="recommendation-tabs" aria-label="추천 시간대 선택">
            {Object.entries(RECOMMENDATION_TABS).map(([key, tab]) => (
              <button
                key={key}
                className={
                  recommendationMode === key
                    ? "recommendation-tab active"
                    : "recommendation-tab"
                }
                onClick={() => handleRecommendationTabClick(key)}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="restaurant-grid">
          {topRestaurants.map((restaurant) => (
            <HomeRestaurantCard
              key={restaurant.id}
              restaurant={restaurant}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

export default HomePage;
