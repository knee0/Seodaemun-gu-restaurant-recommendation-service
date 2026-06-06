import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import HomeRestaurantCard from "../components/HomeRestaurantCard";

function HomePage() {
  const [restaurants, setRestaurants] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [recommendationMode, setRecommendationMode] = useState("lunch");
  const categoryRailRefs = useRef({});
  const navigate = useNavigate();

  const categoryOrder = [
    "한식",
    "중식",
    "일식",
    "양식",
    "카페/디저트",
    "분식/간편식",
    "술집/주점"
  ];

  const recommendationTabs = {
    lunch: {
      label: "점심 추천",
      flag: "is_lunch_recommended"
    },
    dinner: {
      label: "저녁 추천",
      flag: "is_dinner_recommended"
    }
  };

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

  const getDisplayScore = (restaurant) =>
    `${Math.round((restaurant.total_score || 0) * 20)}점`;

  const getCategoryRestaurants = (category) =>
    restaurants
      .filter((restaurant) => restaurant.category === category)
      .sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
      .slice(0, 12);

  const scrollCategoryRail = (category, direction) => {
    const rail = categoryRailRefs.current[category];
    if (!rail) return;

    rail.scrollBy({
      left: direction * Math.round(rail.clientWidth * 0.8),
      behavior: "smooth"
    });
  };

  const activeRecommendation = recommendationTabs[recommendationMode];
  const topRestaurants = restaurants
    .filter((restaurant) => restaurant[activeRecommendation.flag] === true)
    .sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
    .slice(0, 5);

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
          {categoryOrder.map((category, index) => {
            const categoryRestaurants = getCategoryRestaurants(category);

            if (categoryRestaurants.length === 0) {
              return null;
            }

            return (
              <section className="category-rail-section" key={category}>
                <div className="category-rail-header">
                  <h3>
                    <span>{index + 1}.</span> {category}
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
          <h2 className="section-title">{activeRecommendation.label} TOP 5</h2>

          <div className="recommendation-tabs" aria-label="추천 시간대 선택">
            {Object.entries(recommendationTabs).map(([key, tab]) => (
              <button
                key={key}
                className={
                  recommendationMode === key
                    ? "recommendation-tab active"
                    : "recommendation-tab"
                }
                onClick={() => setRecommendationMode(key)}
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
