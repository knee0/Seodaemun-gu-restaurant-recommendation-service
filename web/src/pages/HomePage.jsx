import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import HomeRestaurantCard from "../components/HomeRestaurantCard";

function HomePage() {
  const [restaurants, setRestaurants] = useState([]);
  const navigate = useNavigate();

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
  

  const topRestaurants = restaurants.slice(0, 6);

  return (
    <div className="home-page">
      <section className="hero-section">
        <h1>당신의 취향에 맞는 맛집을 찾아보세요</h1>
        <p>5가지 평가 기준으로 맞춤 추천을 받을 수 있습니다</p>

        <div className="search-bar-wrapper">
          <input type="text" placeholder="맛집 검색..." />
          <button onClick={() => navigate("/preferences")}>맞춤 검색</button>
        </div>
      </section>

      <section className="top-section">
        <h2 className="section-title">인기 맛집 TOP 6</h2>

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