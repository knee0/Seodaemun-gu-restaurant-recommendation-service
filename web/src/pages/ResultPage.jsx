import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import ResultRestaurantCard from "../components/ResultRestaurantCard";

function ResultPage() {
  const [restaurants, setRestaurants] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);

  const selectedCategory = params.get("category") || "전체";
  const priorityParam = params.get("priority") || "";
  const initialSearch = params.get("search") || "";
  const sortOption = params.get("sort") || "recommendation";

  const franchiseParam = params.get("franchise") || "all";
  const [draftFranchise, setDraftFranchise] = useState(franchiseParam);

  const priorityOrder = priorityParam
    ? priorityParam.split(",").filter(Boolean)
    : [];

  const [searchTerm, setSearchTerm] = useState(initialSearch);

  const categories = ["전체", "한식", "양식", "일식", "카페"];

  const priorityItems = [
    { key: "taste", label: "맛" },
    { key: "price", label: "가격" },
    { key: "mood", label: "분위기" },
    { key: "service", label: "서비스" }
  ];

  const [draftCategory, setDraftCategory] = useState(selectedCategory);
  const [draftSearch, setDraftSearch] = useState(initialSearch);
  const [draftSelectedKeys, setDraftSelectedKeys] = useState(priorityOrder);

  const labelMap = {
    taste: "맛",
    price: "가격",
    mood: "분위기",
    service: "서비스"
  };

  //call restaurant data from JSON 
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

  useEffect(() => {
    setDraftCategory(selectedCategory);
    setDraftSearch(initialSearch);
    setDraftSelectedKeys(priorityOrder);
    setSearchTerm(initialSearch);
    setDraftFranchise(franchiseParam);
  }, [selectedCategory, initialSearch, priorityParam, franchiseParam]);

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
        restaurant.menu?.some((menuItem) =>
          menuItem.toLowerCase().includes(keyword)
    ) || false;

      return (
        restaurant.name.toLowerCase().includes(keyword) ||
        restaurant.description.toLowerCase().includes(keyword) ||
        restaurant.category.toLowerCase().includes(keyword) || 
        menuMatched
      );
    })

    .filter((restaurant) => {
      if (franchiseParam == "all") return true;
      if (franchiseParam == "yes") return restaurant.is_franchise == true;
      if (franchiseParam == "no") return restaurant.is_franchise == false;
      return true;
    })

  const allScoreKeys = ["taste", "price", "mood", "service"];

  //calc
  const scoredRestaurants = filteredRestaurants.map((restaurant) => {
    let recommendationScore = 0;

    if (priorityOrder.length === 0) {
      const equalWeight = 1 / allScoreKeys.length;

      recommendationScore = allScoreKeys.reduce((sum, key) => {
        return sum + (restaurant.scores[key] || 0) * equalWeight;
      }, 0);
    } else {
      //place chosen 우선순위 contents to high prio
      //some may not be checked
      const uncheckedKeys = allScoreKeys.filter(
        (key) => !priorityOrder.includes(key)
      );

      const finalOrder = [...priorityOrder, ...uncheckedKeys];
      const weights = [0.35, 0.25, 0.18, 0.12, 0.10];

      recommendationScore = finalOrder.reduce((sum, key, index) => {
        const weight = weights[index] || 0;
        const score = restaurant.scores[key] || 0;
        return sum + score * weight;
      }, 0);
    }

    return {
      ...restaurant,
      recommendationScore: Number(recommendationScore.toFixed(2))
    };
  });

  //sorting restaurant cards
  const rankedRestaurants = [...scoredRestaurants].sort((a, b) => {
    if (sortOption === "reviews") {
      return b.review_count - a.review_count;
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
    priority = priorityParam,
    search = searchTerm,
    sort = sortOption,
    franchise = franchiseParam
  }) => {
    navigate(
      `/results?category=${encodeURIComponent(category)}&priority=${priority}&search=${encodeURIComponent(search)}&sort=${sort}&franchise=${franchise}`    
    );
  };

  const handleSearchSubmit = () => {
    updateUrl({ search: searchTerm });
  };

  const handleSortChange = (newSort) => {
    updateUrl({ sort: newSort });
  };

  const handleTogglePriority = (key) => {
    setDraftSelectedKeys((prev) => {
      if (prev.includes(key)) {
        return prev.filter((item) => item !== key);
      }
      return [...prev, key];
    });
  };

  //advanced settings: apply to URL and close panel
  const handleApplyAdvanced = () => {
    const newPriority = draftSelectedKeys.join(",");

    navigate(
      `/results?category=${encodeURIComponent(
        draftCategory
      )}&priority=${newPriority}&search=${encodeURIComponent(
        draftSearch
      )}&sort=${sortOption}&franchise=${draftFranchise}`
    );

    setShowAdvanced(false);
  };

  //우선순위 텍스트는 3개만
  const shortPriorityText =
    priorityOrder.length > 0
      ? priorityOrder.map((key) => labelMap[key]).slice(0, 3).join(" > ")
      : "없음";

  const draftPriorityPreview = useMemo(() => {
    if (draftSelectedKeys.length === 0) return "없음";

    return draftSelectedKeys
      .map((key) => priorityItems.find((item) => item.key === key)?.label)
      .join(" > ");
  }, [draftSelectedKeys]);

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
          <button
            className="advanced-button"
            onClick={() => setShowAdvanced((prev) => !prev)}
          >
            고급설정
          </button>
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
          <span className="info-chip">우선순위: {shortPriorityText}</span>
        </div>

        <div className={`advanced-panel ${showAdvanced ? "open" : ""}`}>
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
              <h3>중요한 평가 기준 선택</h3>
              <p>체크한 순서대로 우선 반영됩니다.</p>

              <div className="compact-priority-list">
                {priorityItems.map((item) => {
                  const checked = draftSelectedKeys.includes(item.key);
                  const order = checked
                    ? draftSelectedKeys.indexOf(item.key) + 1
                    : null;

                  return (
                    <button
                      key={item.key}
                      type="button"
                      className={
                        checked
                          ? "compact-priority-chip active"
                          : "compact-priority-chip"
                      }
                      onClick={() => handleTogglePriority(item.key)}
                    >
                      <span className="chip-checkbox">{checked ? "✓" : ""}</span>
                      <span className="chip-label">{item.label}</span>
                      {checked && <span className="chip-order">{order}</span>}
                    </button>
                  );
                })}
              </div>

              <div className="selected-priority-preview">
                <strong>현재 우선순위:</strong> {draftPriorityPreview}
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