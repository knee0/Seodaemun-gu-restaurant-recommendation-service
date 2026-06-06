import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import ResultRestaurantCard from "../components/ResultRestaurantCard";

function ResultPage() {
  const [restaurants, setRestaurants] = useState([]);

  const location = useLocation();
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);

  const selectedCategory = params.get("category") || "전체";
  const initialSearch = params.get("search") || "";
  const sortOption = params.get("sort") || "recommendation";

  const franchiseParam = params.get("franchise") || "all";
  const [draftFranchise, setDraftFranchise] = useState(franchiseParam);

  const hasCustomWeights =
  params.has("taste") ||
  params.has("price") ||
  params.has("mood") ||
  params.has("service");

  const tasteWeight = Number(params.get("taste") || 1);
  const priceWeight = Number(params.get("price") || 1);
  const moodWeight = Number(params.get("mood") || 1);
  const serviceWeight = Number(params.get("service") || 1);

  const weightValues = {
    taste: tasteWeight,
    price: priceWeight,
    mood: moodWeight,
    service: serviceWeight
  };

  const [searchTerm, setSearchTerm] = useState(initialSearch);

  const categories = [
    "전체",
    "한식",
    "중식",
    "일식",
    "양식",
    "카페/디저트",
    "분식/간편식",
    "술집/주점"
  ];

  const weightItems = [
    { key: "taste", label: "음식" },
    { key: "price", label: "가격" },
    { key: "mood", label: "분위기" },
    { key: "service", label: "서비스" }
  ];

  const [draftCategory, setDraftCategory] = useState(selectedCategory);

  const [draftWeights, setDraftWeights] = useState({
    taste: tasteWeight,
    price: priceWeight,
    mood: moodWeight,
    service: serviceWeight
  });

  const scoreItems = [
    { weightKey: "taste", scoreKey: "food", label: "음식" },
    { weightKey: "price", scoreKey: "price", label: "가격" },
    { weightKey: "mood", scoreKey: "mood", label: "분위기" },
    { weightKey: "service", scoreKey: "service", label: "서비스" }
  ];

  const getScoreValue = (restaurant, scoreKey) =>
    Number(restaurant.scores?.[scoreKey] || 0);

  const getIsFranchise = (restaurant) => {
    if (typeof restaurant.is_franchise === "boolean") {
      return restaurant.is_franchise;
    }

    if (typeof restaurant.is_franchise === "string") {
      return restaurant.is_franchise.toLowerCase() === "true";
    }

    return false;
  };

  //call restaurant data from JSON
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

  useEffect(() => {
    setDraftCategory(selectedCategory);
    setSearchTerm(initialSearch);
    setDraftFranchise(franchiseParam);
    setDraftWeights({
      taste: tasteWeight,
      price: priceWeight,
      mood: moodWeight,
      service: serviceWeight
    });
  }, [
    selectedCategory,
    initialSearch,
    franchiseParam,
    tasteWeight,
    priceWeight,
    moodWeight,
    serviceWeight
  ]);

  const filteredRestaurants = restaurants
    //filter category
    .filter((restaurant) => {
      if (selectedCategory === "전체") return true;
      return restaurant.category === selectedCategory;
    })
    //filter seach bar content
    .filter((restaurant) => {
      if (!searchTerm.trim()) return true;

      const keyword = searchTerm.toLowerCase();

      const menuMatched =
        restaurant.menus?.some((menuItem) =>
          menuItem.toLowerCase().includes(keyword)
        ) || false;

      const searchableText = [
        restaurant.name,
        restaurant.description,
        restaurant.category,
        restaurant.category_raw,
        restaurant.address
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return (
        searchableText.includes(keyword) || menuMatched
      );
    })
    .filter((restaurant) => {
      if (franchiseParam === "all") return true;
      if (franchiseParam === "yes") return getIsFranchise(restaurant);
      if (franchiseParam === "no") return !getIsFranchise(restaurant);
      return true;
    });

  //calc
  const scoredRestaurants = filteredRestaurants.map((restaurant) => {
    let weightedScore = 0;

    const rawWeights = scoreItems.map((item) => weightValues[item.weightKey] || 0);
    const totalWeight = rawWeights.reduce((sum, value) => sum + value, 0);

    //no weights = no advanced setting
    if (!hasCustomWeights) {
      const equalWeight = 1 / scoreItems.length;

      weightedScore = scoreItems.reduce((sum, item) => {
        return sum + getScoreValue(restaurant, item.scoreKey) * equalWeight;
      }, 0);
    } else {
      //유저 설정 가중치
      weightedScore = scoreItems.reduce((sum, item) => {
        const normalizedWeight =
          totalWeight > 0 ? (weightValues[item.weightKey] || 0) / totalWeight : 0;
        return sum + getScoreValue(restaurant, item.scoreKey) * normalizedWeight;
      }, 0);
    }

    return {
      ...restaurant,
      recommendationScore: Number(weightedScore.toFixed(2))
    };
  });

  //sorting restaurant cards
  const rankedRestaurants = [...scoredRestaurants].sort((a, b) => {
    if (sortOption === "reviews") {
      return (b.review_count || 0) - (a.review_count || 0);
    }

    if (sortOption === "rating") {
      return b.total_score - a.total_score;
    }

    if (sortOption === "name") {
      return a.name.localeCompare(b.name, "ko");
    }

    return b.recommendationScore - a.recommendationScore;
  });

  //update URL to match with selected values
  const updateUrl = ({
    category = selectedCategory,
    search = searchTerm,
    sort = sortOption,
    franchise = franchiseParam,
    taste = tasteWeight,
    price = priceWeight,
    mood = moodWeight,
    service = serviceWeight
  }) => {
    navigate(
      `/results?category=${encodeURIComponent(
        category
      )}&search=${encodeURIComponent(
        search
      )}&sort=${sort}&franchise=${franchise}&taste=${taste}&price=${price}&mood=${mood}&service=${service}`
    );
  };

  const handleSearchSubmit = () => {
    updateUrl({ search: searchTerm });
  };

  const handleSortChange = (newSort) => {
    updateUrl({ sort: newSort });
  };

  const handleWeightChange = (key, value) => {
    setDraftWeights((prev) => ({
      ...prev,
      [key]: Number(value)
    }));
  };

  //advanced settings: apply to URL
  const handleApplyAdvanced = () => {
    navigate(
      `/results?category=${encodeURIComponent(
        draftCategory
      )}&search=${encodeURIComponent(
        searchTerm
      )}&sort=${sortOption}&franchise=${draftFranchise}&taste=${
        draftWeights.taste
      }&price=${draftWeights.price}&mood=${draftWeights.mood}&service=${
        draftWeights.service
      }`
    );
  };

  //show current weight values
  const shortPriorityText = useMemo(() => {
    const activeWeights = weightItems
      .filter((item) => weightValues[item.key] > 0)
      .map((item) => `${item.label} ${weightValues[item.key]}`);

    return activeWeights.length > 0 ? activeWeights.join(" · ") : "없음";
  }, [tasteWeight, priceWeight, moodWeight, serviceWeight]);

  const draftPriorityPreview = useMemo(() => {
    const activeWeights = weightItems
      .filter((item) => draftWeights[item.key] > 0)
      .map((item) => `${item.label} ${draftWeights[item.key]}`);

    return activeWeights.length > 0 ? activeWeights.join(" · ") : "없음";
  }, [draftWeights]);

  return (
    <div className="result-page">
      <div className="result-top-bar">
        <button onClick={() => navigate("/")}>← 뒤로가기</button>
      </div>

      <section className="result-section">
        <h2 className="section-title">
          맞춤 추천 결과 ({rankedRestaurants.length}개)
        </h2>

        <div className="result-search-row">
          <input
            type="text"
            placeholder="맛집 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearchSubmit();
            }}
          />
          <button onClick={handleSearchSubmit}>검색</button>
        </div>

        <div className="result-info-bar">
          <span className="info-chip">
            프랜차이즈: {
              franchiseParam === "all"
                ? "전체"
                : franchiseParam === "yes"
                ? "프랜차이즈만"
                : "비프랜차이즈만"
            }
          </span>
          <span className="info-chip">카테고리: {selectedCategory}</span>
          <span className="info-chip">가중치: {shortPriorityText}</span>
        </div>

        <div className="advanced-panel open result-settings-panel">
          <div className="advanced-panel-inner">
            <div className="advanced-block">
              <h3>카테고리</h3>
              <div className="category-list">
                {categories.map((category) => (
                  <button
                    key={category}
                    className={
                      draftCategory === category
                        ? "category-button active"
                        : "category-button"
                    }
                    onClick={() => setDraftCategory(category)}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            <div className="advanced-block">
              <h3>평가 항목 가중치 설정</h3>
              <p>각 항목에 1~5 값을 주면, 그 비율대로 총점이 계산됩니다.</p>

              <div className="weight-setting-list">
                {weightItems.map((item) => (
                  <div key={item.key} className="weight-setting-row">
                    <span className="weight-setting-label">{item.label}</span>

                    <div className="weight-slider-group">
                      <input
                        type="range"
                        min="1"
                        max="5"
                        step="1"
                        value={draftWeights[item.key]}
                        onChange={(e) => handleWeightChange(item.key, e.target.value)}
                        className="weight-slider"
                      />
                      <span className="weight-slider-value">{draftWeights[item.key]}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="selected-priority-preview">
                <strong>현재 가중치:</strong> {draftPriorityPreview}
              </div>
            </div>

            <div className="advanced-block">
              <h3>프랜차이즈 여부</h3>
              <div className="category-list">
                <button
                  className={draftFranchise === "all" ? "category-button active" : "category-button"}
                  onClick={() => setDraftFranchise("all")}
                >
                  전체
                </button>
                <button
                  className={draftFranchise === "yes" ? "category-button active" : "category-button"}
                  onClick={() => setDraftFranchise("yes")}
                >
                  프랜차이즈만
                </button>
                <button
                  className={draftFranchise === "no" ? "category-button active" : "category-button"}
                  onClick={() => setDraftFranchise("no")}
                >
                  비프랜차이즈만
                </button>
              </div>
            </div>

            <div className="advanced-actions">
              <button className="result-button" onClick={handleApplyAdvanced}>
                적용하기
              </button>
            </div>
          </div>
        </div>

        <div className="sort-chip-row">
          <span className="sort-chip-label">정렬 기준</span>

          <button
            className={
              sortOption === "recommendation"
                ? "sort-chip active"
                : "sort-chip"
            }
            onClick={() => handleSortChange("recommendation")}
          >
            추천순
          </button>

          <button
            className={sortOption === "rating" ? "sort-chip active" : "sort-chip"}
            onClick={() => handleSortChange("rating")}
          >
            평점순
          </button>

          <button
            className={sortOption === "reviews" ? "sort-chip active" : "sort-chip"}
            onClick={() => handleSortChange("reviews")}
          >
            리뷰 많은순
          </button>

          <button
            className={sortOption === "name" ? "sort-chip active" : "sort-chip"}
            onClick={() => handleSortChange("name")}
          >
            이름순
          </button>
        </div>

        {rankedRestaurants.length === 0 ? (
          <div className="empty-result-box">
            <h3>검색 결과가 없습니다</h3>
          </div>
        ) : (
          <div className="restaurant-grid">
            {rankedRestaurants.map((restaurant) => (
              <ResultRestaurantCard
                key={restaurant.id}
                restaurant={restaurant}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default ResultPage;
