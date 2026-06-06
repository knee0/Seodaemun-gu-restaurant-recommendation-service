import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import RestaurantImage from "../components/RestaurantImage";
import StarRating from "../components/StarRating";

const normalizeCategory = (category) =>
  category === "세계요리" ? "아시안/세계요리" : category;

function DetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState(null);

  //fetch restaurant data from restaurant ID in URL
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/web_format_scores.json`)
      .then((response) => response.json())
      .then((data) => {
        const found = data.find((item) => item.id === id);
        setRestaurant(found || null);
      })
      .catch((error) => {
        console.error("상세 데이터를 불러오는 데 실패했습니다:", error);
      });
  }, [id]);

  if (!restaurant) {
    return (
      <div className="detail-page">
        <div className="detail-container">
          <button className="detail-back-button" onClick={() => navigate(-1)}>
            ← 뒤로가기
          </button>
          <p>식당 정보를 찾을 수 없습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="detail-page">
      <div className="detail-container">
        <button className="detail-back-button" onClick={() => navigate(-1)}>
          ← 뒤로가기
        </button>

        <RestaurantImage restaurant={restaurant} variant="detail" />

        <div className="detail-header">
          <div>
            <h1>{restaurant.name}</h1>
            <p className="detail-description">
              {restaurant.description || restaurant.category_raw || restaurant.address}
            </p>
          </div>
          <span className="category-badge">{normalizeCategory(restaurant.category)}</span>
        </div>

        <div className="detail-rating-summary">
          <StarRating score={restaurant.total_score} />
          {typeof restaurant.review_count === "number" && (
            <span className="detail-review-count">({restaurant.review_count}개 리뷰)</span>
          )}
        </div>

        <section className="detail-section">
          <h2>카테고리별 평점</h2>
          <div className="detail-score-list">
            <div className="detail-score-row">
              <span className="detail-score-label">음식</span>
              <StarRating score={restaurant.scores.food} />
            </div>
            <div className="detail-score-row">
              <span className="detail-score-label">분위기</span>
              <StarRating score={restaurant.scores.mood} />
            </div>
            <div className="detail-score-row">
              <span className="detail-score-label">가격</span>
              <StarRating score={restaurant.scores.price} />
            </div>
            <div className="detail-score-row">
              <span className="detail-score-label">서비스</span>
              <StarRating score={restaurant.scores.service} />
            </div>
          </div>
        </section>

        <section className="detail-section">
          <h2>상세 정보</h2>
          <div className="detail-info-list">
            <p>📍 {restaurant.address || "주소 정보 없음"}</p>
          </div>

          <div className="detail-map-buttons">
            <a
              href={restaurant.naver_url || "#"}
              target="_blank"
              rel="noreferrer"
              className="naver-map-button"
            >
              네이버 지도로 보기
            </a>

          </div>
        </section>
      </div>
    </div>
  );
}

export default DetailPage;
