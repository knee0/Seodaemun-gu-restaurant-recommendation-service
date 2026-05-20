import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import ResultRestaurantCard from "../components/ResultRestaurantCard";

function ResultPage() {
  const [restaurants, setRestaurants] = useState([]);
  const location = useLocation();
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);
  const selectedCategory = params.get("category") || "전체";
  const priorityParam =
    params.get("priority") || "taste,price,mood,system,service";

  const priorityOrder = priorityParam.split(",");

  const weights = [0.35, 0.25, 0.18, 0.12, 0.10];

  const labelMap = {
    taste: "맛",
    price: "가격",
    mood: "분위기",
    system: "시스템",
    service: "서비스"
  };

  useEffect(() => {
    fetch("/data/web_mock_restaurants.json")
      .then((response) => response.json())
      .then((data) => {
        setRestaurants(data);
      })
      .catch((error) => {
        console.error("데이터를 불러오는 데 실패했습니다:", error);
      });
  }, []);

  const filteredRestaurants =
    selectedCategory === "전체"
      ? restaurants
      : restaurants.filter(
          (restaurant) => restaurant.category === selectedCategory
        );

  const rankedRestaurants = filteredRestaurants
    .map((restaurant) => {
      const recommendationScore = priorityOrder.reduce((sum, key, index) => {
        const weight = weights[index] || 0;
        const score = restaurant.scores[key] || 0;
        return sum + score * weight;
      }, 0);

      return {
        ...restaurant,
        recommendationScore: recommendationScore.toFixed(2)
      };
    })
    .sort((a, b) => b.recommendationScore - a.recommendationScore);

  return (
    <div className="result-page">
      <div className="result-top-bar">
        <button onClick={() => navigate("/preferences")}>← 뒤로가기</button>
      </div>

      <section className="result-section">
        <h2 className="section-title">
          맞춤 추천 결과 ({rankedRestaurants.length}개)
        </h2>

        <p className="result-subtitle">
          선택한 카테고리: <strong>{selectedCategory}</strong>
        </p>

        <p className="result-subtitle">
          우선순위:{" "}
          <strong>
            {priorityOrder.map((key) => labelMap[key]).join(" > ")}
          </strong>
        </p>

        <div className="restaurant-grid">
          {rankedRestaurants.map((restaurant) => (
            <ResultRestaurantCard
              key={restaurant.id}
              restaurant={restaurant}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

export default ResultPage;