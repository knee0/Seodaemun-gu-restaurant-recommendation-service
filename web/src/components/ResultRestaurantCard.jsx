import { useNavigate } from "react-router-dom";
import StarRating from "./StarRating";

function ResultRestaurantCard({ restaurant }) {
  const navigate = useNavigate();

  //key: internal ops, label: UI
  const scoreLabels = [
    { key: "taste", label: "맛" },
    { key: "price", label: "가격" },
    { key: "mood", label: "분위기" },
    { key: "system", label: "시스템" },
    { key: "service", label: "서비스" }
  ];

  return (
    <div
      className="restaurant-card result-card clickable-card"
      onClick={() => navigate(`/restaurants/${restaurant.id}`)}
    >
      <div className="restaurant-image-placeholder"> 
        {/*TODO*/}
        이미지
      </div>

      <div className="restaurant-card-body">
        <div className="restaurant-card-header">
          <h3>{restaurant.name}</h3>
          <span className="category-badge">{restaurant.category}</span>
        </div>

        <p className="restaurant-description">{restaurant.description}</p>

      <div className="restaurant-meta">
        <StarRating score={restaurant.total_score} />
        <span>리뷰 {restaurant.review_count}개</span>
      </div>

        {restaurant.recommendationScore && (
          <div className="recommendation-score">
            추천 점수 {restaurant.recommendationScore}
          </div>
        )}

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