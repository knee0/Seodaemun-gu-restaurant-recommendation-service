import { useNavigate } from "react-router-dom";

function HomeRestaurantCard({ restaurant }) {
  const navigate = useNavigate();

  return (
    <div
      className="restaurant-card home-card clickable-card"
      onClick={() => navigate(`/restaurants/${restaurant.id}`)}
    >
      <div className="restaurant-image-placeholder">
        이미지
      </div>

      <div className="restaurant-card-body">
        <div className="restaurant-card-header">
          <h3>{restaurant.name}</h3>
          <span className="category-badge">{restaurant.category}</span>
        </div>

        <p className="restaurant-description">{restaurant.description}</p>

        <div className="restaurant-meta">
          <span>총점 {restaurant.total_score}</span>
          <span>리뷰 {restaurant.review_count}개</span>
        </div>
      </div>
    </div>
  );
}

export default HomeRestaurantCard;