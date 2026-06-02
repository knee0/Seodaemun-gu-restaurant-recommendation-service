import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import RestaurantImage from "../components/RestaurantImage";
import StarRating from "../components/StarRating";

//star ratings
function renderStars(rating) {
  const fullStars = "★".repeat(Math.floor(rating));
  const emptyStars = "☆".repeat(5 - Math.floor(rating));
  return fullStars + emptyStars;
}

function DetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState(null);

  //fetch restaurant data from restaurant ID in URL
  useEffect(() => {
    fetch("/data/web_mock_restaurants.json")
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
            <p className="detail-description">{restaurant.description}</p>
          </div>
          <span className="category-badge">{restaurant.category}</span>
        </div>

        <div className="detail-rating-summary">
          <StarRating score={restaurant.total_score} />
          <span className="detail-review-count">({restaurant.review_count}개 리뷰)</span>
        </div>

        <section className="detail-section">
          <h2>카테고리별 평점</h2>
          <div className="detail-score-list">
            <div className="detail-score-row">
              <span className="detail-score-label">맛</span>
              <StarRating score={restaurant.scores.taste} />
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
            <div className="detail-score-row">
              <span className="detail-score-label">편의성</span>
              <StarRating score={restaurant.scores.system} />
            </div>
          </div>
        </section>

        <section className="detail-section">
          <h2>상세 정보</h2>
          <div className="detail-info-list">
            <p>📞 {restaurant.phone || "전화번호 없음"}</p>
            <p>📍 {restaurant.address || "주소 정보 없음"}</p>
          </div>

          <div className="detail-map-buttons">
            <a
              href={restaurant.naver_map_url || "#"}
              target="_blank"
              rel="noreferrer"
              className="naver-map-button"
            >
              네이버 지도로 보기
            </a>

            <a
              href={restaurant.kakao_map_url || "#"}
              target="_blank"
              rel="noreferrer"
              className="kakao-map-button"
            >
              카카오맵으로 보기
            </a>
          </div>
        </section>

        <section className="detail-section">
          <h2>대표 리뷰</h2>

          <div className="review-list">
            {(restaurant.reviews || []).map((review, index) => (
              <div key={index} className="review-card">
                <div className="review-header">
                  <strong>{review.author}</strong>
                  <span>{renderStars(review.rating)}</span>
                  <span>{review.date}</span>
                </div>
                <p>{review.text}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default DetailPage;
