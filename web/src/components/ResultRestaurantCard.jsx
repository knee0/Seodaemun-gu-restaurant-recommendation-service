import { useNavigate } from "react-router-dom";
import RestaurantImage from "./RestaurantImage";
import StarRating from "./StarRating";

function ResultRestaurantCard({ restaurant }) {
  const navigate = useNavigate();

  //key: internal ops, label: UI
  const scoreLabels = [
    { key: "taste", label: "음식" },
    { key: "price", label: "가격" },
    { key: "mood", label: "분위기" },
    { key: "service", label: "서비스" }
  ];

  return (
    <div
      className="restaurant-card result-card clickable-card"
      onClick={() => navigate(`/restaurants/${restaurant.id}`)}
    >
      <RestaurantImage restaurant={restaurant} />

      <div className="restaurant-card-body">
        <div className="restaurant-card-header">
          <h3>{restaurant.name}</h3>
          <span className="category-badge">{restaurant.category}</span>
        </div>

        <p className="restaurant-description">{restaurant.description}</p>

      <div className="restaurant-meta">
        <StarRating score={restaurant.recommendationScore ?? restaurant.total_score} />
        <span>
          맞춤 총점 {(restaurant.recommendationScore ?? restaurant.total_score).toFixed(2)}
        </span>
      </div>

      <div className="restaurant-sub-meta">
        <span>리뷰 {restaurant.review_count}개</span>
      </div>

        <div className="detail-score-list">
          {scoreLabels.map((item) => (
            <div key={item.key} className="detail-score-row">
              <span className="detail-score-label">{item.label}</span>
              <StarRating score={restaurant.scores[item.key]} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default ResultRestaurantCard;
