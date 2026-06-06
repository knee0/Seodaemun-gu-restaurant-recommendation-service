import { useNavigate } from "react-router-dom";
import RestaurantImage from "./RestaurantImage";
import StarRating from "./StarRating";

function HomeRestaurantCard({ restaurant }) {
  const navigate = useNavigate();
  const description = restaurant.description || restaurant.category_raw || restaurant.address;

  return (
    <div
      className="restaurant-card home-card clickable-card"
      onClick={() => navigate(`/restaurants/${restaurant.id}`)}
    >
      <RestaurantImage restaurant={restaurant} />

      <div className="restaurant-card-body">
        <div className="restaurant-card-header">
          <h3>{restaurant.name}</h3>
          <span className="category-badge">{restaurant.category}</span>
        </div>

        {description && <p className="restaurant-description">{description}</p>}

        <div className="restaurant-meta">
          <StarRating score={restaurant.total_score} />
          {typeof restaurant.review_count === "number" && (
            <span>리뷰 {restaurant.review_count}개</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default HomeRestaurantCard;
