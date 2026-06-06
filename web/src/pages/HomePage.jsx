import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import HomeRestaurantCard from "../components/HomeRestaurantCard";

function HomePage() {
  const [restaurants, setRestaurants] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [recommendationMode, setRecommendationMode] = useState("lunch");
  const navigate = useNavigate();

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
