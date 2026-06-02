import { useMemo, useState } from "react";

function getRestaurantImageUrl(restaurant) {
  return (
    restaurant.thumbnail_url ||
    restaurant.thumbnailUrl ||
    restaurant.image_url ||
    restaurant.imageUrl ||
    ""
  );
}

function getInitialText(name) {
  const trimmed = (name || "").trim();
  if (!trimmed) return "맛집";
  return [...trimmed].slice(0, 2).join("");
}

function RestaurantImage({ restaurant, variant = "card" }) {
  const [imageFailed, setImageFailed] = useState(false);
  const imageUrl = getRestaurantImageUrl(restaurant);
  const initialText = useMemo(() => getInitialText(restaurant.name), [restaurant.name]);
  const className = `restaurant-image restaurant-image-${variant}`;

  if (imageUrl && !imageFailed) {
    return (
      <div className={className}>
        <img
          src={imageUrl}
          alt={`${restaurant.name} 대표 이미지`}
          loading="lazy"
          onError={() => setImageFailed(true)}
        />
      </div>
    );
  }

  return (
    <div className={`${className} restaurant-image-fallback`} aria-label={`${restaurant.name} 대표 이미지 없음`}>
      <span>{initialText}</span>
    </div>
  );
}

export default RestaurantImage;
