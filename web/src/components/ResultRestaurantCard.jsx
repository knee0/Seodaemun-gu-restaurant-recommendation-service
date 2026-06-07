import { useNavigate } from "react-router-dom";
import RestaurantImage from "./RestaurantImage";
import StarRating from "./StarRating";

const normalizeCategory = (category) =>
  category === "세계요리" ? "아시안/세계요리" : category;

function ResultRestaurantCard({ restaurant }) {
  const navigate = useNavigate();
  const mainScore = restaurant.recommendationScore ?? restaurant.total_score ?? 0;
  const description = restaurant.description || restaurant.category_raw || restaurant.address;

  //key: internal ops, label: UI
  const scoreLabels = [
    { key: "food", label: "음식" },
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
          <span className="category-badge">{normalizeCategory(restaurant.category)}</span>
        </div>

        {description && <p className="restaurant-description">{description}</p>}

        <div className="custom-score-panel">
          <span className="custom-score-label">맞춤 총점</span>
          <strong className="custom-score-value">{mainScore <= 0 ? "?" : mainScore.toFixed(2)}</strong>
          <StarRating score={mainScore} />
        </div>

        <div className="restaurant-sub-meta">
          <span>기본 평점 {restaurant.total_score === -1 ? "?" : restaurant.total_score?.toFixed(1)} </span>
          {typeof restaurant.review_count === "number" && (
            <span>리뷰 {restaurant.review_count}개</span>
          )}
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
