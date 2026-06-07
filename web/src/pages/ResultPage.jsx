import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import ResultRestaurantCard from "../components/ResultRestaurantCard";

function ResultPage() {
  const [restaurants, setRestaurants] = useState([]);
  const [foodDictionary, setFoodDictionary] = useState({});

  const location = useLocation();
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);
  const hasCategoryParam = params.has("category");

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
    "술집/주점",
    "아시안/세계요리"
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

  const normalizeText = (value) =>
    String(value || "")
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();

  const splitSearchTerms = (value) =>
    normalizeText(value)
      .split(" ")
      .map((term) => term.trim())
      .filter(Boolean);

  const getRestaurantSearchFields = (restaurant) => [
    restaurant.name,
    restaurant.category,
    restaurant.category_raw,
    ...(Array.isArray(restaurant.menus) ? restaurant.menus : [])
  ];

  const restaurantMatchesTerm = (restaurant, term) => {
    const normalizedTerm = normalizeText(term);
    if (!normalizedTerm) return false;

    return getRestaurantSearchFields(restaurant).some((field) =>
      normalizeText(field).includes(normalizedTerm)
    );
  };

  const getCategoryRank = (category) => {
    const index = categories.indexOf(category);
    return index === -1 ? categories.length : index;
  };

  const normalizeCategory = (category) =>
    category === "세계요리" ? "아시안/세계요리" : category;

  const categoryMatches = (restaurantCategory, category) => {
    if (category === "전체") return true;
    return normalizeCategory(restaurantCategory) === category;
  };

  const getDominantCategory = (matchedRestaurants) => {
    const counts = matchedRestaurants.reduce((acc, restaurant) => {
      const category = normalizeCategory(restaurant.category);
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(counts).sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1];
      return getCategoryRank(a[0]) - getCategoryRank(b[0]);
    })[0]?.[0] || "전체";
  };

  const dictionaryEntryMatchesTerm = (entry, term) => {
    const normalizedEntry = normalizeText(entry);
    const normalizedTerm = normalizeText(term);
    return Boolean(normalizedEntry && normalizedTerm && normalizedEntry.includes(normalizedTerm));
  };

  const inferCategoryFromDictionary = (terms) => {
    const matches = Object.entries(foodDictionary).map(([category, words]) => {
      const wordList = Array.isArray(words) ? words : [];
      const matchCount = terms.reduce((count, term) => {
        const hasMatch = wordList.some((word) => dictionaryEntryMatchesTerm(word, term));
        return hasMatch ? count + 1 : count;
      }, 0);

      return {
        category: normalizeCategory(category),
        matchCount
      };
    });

    return matches
      .filter((match) => match.matchCount > 0)
      .sort((a, b) => {
        if (b.matchCount !== a.matchCount) return b.matchCount - a.matchCount;
        return getCategoryRank(a.category) - getCategoryRank(b.category);
      })[0]?.category || null;
  };

  const analyzeSearch = (search) => {
    const normalizedSearch = normalizeText(search);

    if (!normalizedSearch) {
      return {
        type: "none",
        matchedRestaurants: null,
        inferredCategory: null
      };
    }

    const fullTermMatches = restaurants.filter((restaurant) =>
      restaurantMatchesTerm(restaurant, normalizedSearch)
    );

    if (fullTermMatches.length > 0) {
      return {
        type: "restaurant",
        matchedRestaurants: fullTermMatches,
        inferredCategory: getDominantCategory(fullTermMatches)
      };
    }

    const splitTerms = splitSearchTerms(normalizedSearch);
    const splitTermMatches = restaurants.filter((restaurant) =>
      splitTerms.some((term) => restaurantMatchesTerm(restaurant, term))
    );

    if (splitTermMatches.length > 0) {
      return {
        type: "restaurant",
        matchedRestaurants: splitTermMatches,
        inferredCategory: getDominantCategory(splitTermMatches)
      };
    }

    const fullDictionaryCategory = inferCategoryFromDictionary([normalizedSearch]);

    if (fullDictionaryCategory) {
      return {
        type: "dictionary",
        matchedRestaurants: null,
        inferredCategory: fullDictionaryCategory
      };
    }

    const splitDictionaryCategory = inferCategoryFromDictionary(splitTerms);

    return {
      type: splitDictionaryCategory ? "dictionary" : "none",
      matchedRestaurants: null,
      inferredCategory: splitDictionaryCategory
    };
  };

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
    Promise.all([
      fetch(`${import.meta.env.BASE_URL}data/web_format_scores.json`).then((response) =>
        response.json()
      ),
      fetch(`${import.meta.env.BASE_URL}data/food_dictionary.json`).then((response) =>
        response.json()
      )
    ])
      .then(([restaurantData, dictionaryData]) => {
        setRestaurants(restaurantData);
        setFoodDictionary(dictionaryData);
      })
      .catch((error) => {
        console.error("데이터를 불러오는 데 실패했습니다:", error);
      });
  }, []);

  const searchAnalysis = analyzeSearch(initialSearch);
  const effectiveCategory =
    hasCategoryParam ? selectedCategory : searchAnalysis.inferredCategory || selectedCategory;

  useEffect(() => {
    setDraftCategory(effectiveCategory);
    setSearchTerm(initialSearch);
    setDraftFranchise(franchiseParam);
    setDraftWeights({
      taste: tasteWeight,
      price: priceWeight,
      mood: moodWeight,
      service: serviceWeight
    });
  }, [
    effectiveCategory,
    initialSearch,
    franchiseParam,
    tasteWeight,
    priceWeight,
    moodWeight,
    serviceWeight
  ]);

  const searchCandidateRestaurants =
    initialSearch.trim() && searchAnalysis.type === "restaurant"
      ? searchAnalysis.matchedRestaurants
      : restaurants;

  const filteredRestaurants = searchCandidateRestaurants
    .filter((restaurant) => categoryMatches(restaurant.category, effectiveCategory))
    .filter((restaurant) => {
      if (!initialSearch.trim()) return true;
      if (searchAnalysis.type === "restaurant") return true;
      if (searchAnalysis.type === "dictionary") return true;
      return false;
    })
    .filter((restaurant) => {
      if (franchiseParam === "all") return true;
      if (franchiseParam === "yes") return getIsFranchise(restaurant);
      if (franchiseParam === "no") return !getIsFranchise(restaurant);
      return true;
    });


  //calc
  let finalWeights = [];

  if (!hasCustomWeights) {
    const equalWeight = 1 / scoreItems.length;
    finalWeights = scoreItems.map(() => equalWeight);
  } else {
    const rawWeights = scoreItems.map((item) => weightValues[item.weightKey] || 0);
    const totalWeight = rawWeights.reduce((sum, value) => sum + value, 0);

    // Pre-normalize weights for no division inside restaurant loop
    finalWeights = scoreItems.map((item) => 
      totalWeight > 0 ? (weightValues[item.weightKey] || 0) / totalWeight : 0
    );
  }

  const scoredRestaurants = filteredRestaurants.map((restaurant) => {
   const weightedScore = scoreItems.reduce((sum, item, index) => {
    return sum + getScoreValue(restaurant, item.scoreKey) * finalWeights[index];
  }, 0);

    return {
      ...restaurant,
      // Keep raw float for accurate sorting
      recommendationScore: weightedScore 
    };
  });

  //sorting restaurant cards
  const rankedRestaurants = [...scoredRestaurants].sort((a, b) => {
    if (sortOption === "reviews") {
      return (b.review_count || 0) - (a.review_count || 0);
    }

    if (sortOption === "rating") {
      const ratingDiff = (b.total_score || 0) - (a.total_score || 0);
      if (ratingDiff !== 0) return ratingDiff;
      return b.recommendationScore - a.recommendationScore;
    }

    if (sortOption === "name") {
      return a.name.localeCompare(b.name, "ko");
    }

    return b.recommendationScore - a.recommendationScore;
  });

  //update URL to match with selected values
  const updateUrl = ({
    category = effectiveCategory,
    search = searchTerm,
    sort = sortOption,
    franchise = franchiseParam,
    taste = tasteWeight,
    price = priceWeight,
    mood = moodWeight,
    service = serviceWeight
  }, options = {}) => {
    const { replace = false } = options;

    navigate(
      `/results?category=${encodeURIComponent(
        category
      )}&search=${encodeURIComponent(
        search
      )}&sort=${sort}&franchise=${franchise}&taste=${taste}&price=${price}&mood=${mood}&service=${service}`,
      { replace }
    );
  };

  const handleSearchSubmit = () => {
    const nextSearchAnalysis = analyzeSearch(searchTerm);
    const nextCategory = nextSearchAnalysis.inferredCategory || effectiveCategory;

    setDraftCategory(nextCategory);
    updateUrl({ category: nextCategory, search: searchTerm });
  };

  const handleSortChange = (newSort) => {
    updateUrl({ sort: newSort });
  };

  const handleCategoryChange = (category) => {
    setDraftCategory(category);
    updateUrl({ category }, { replace: true });
  };

  const handleFranchiseChange = (franchise) => {
    setDraftFranchise(franchise);
    updateUrl({ franchise }, { replace: true });
  };

  const handleWeightChange = (key, value) => {
    const nextWeights = {
      ...draftWeights,
      [key]: Number(value)
    };

    setDraftWeights(nextWeights);
    updateUrl(
      {
        taste: nextWeights.taste,
        price: nextWeights.price,
        mood: nextWeights.mood,
        service: nextWeights.service
      },
      { replace: true }
    );
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
          <span className="info-chip">카테고리: {effectiveCategory}</span>
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
                    onClick={() => handleCategoryChange(category)}
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
                  onClick={() => handleFranchiseChange("all")}
                >
                  전체
                </button>
                <button
                  className={draftFranchise === "yes" ? "category-button active" : "category-button"}
                  onClick={() => handleFranchiseChange("yes")}
                >
                  프랜차이즈만
                </button>
                <button
                  className={draftFranchise === "no" ? "category-button active" : "category-button"}
                  onClick={() => handleFranchiseChange("no")}
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
