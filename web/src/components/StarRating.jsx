function StarRating({ score }) {
  /* visualise star ratings
  floor rating data in 0.5 intervals & display stars
  user still sees original data, not floored
  */
  const flooredToHalf = Math.floor(score * 2) / 2;
  const percentage = (flooredToHalf / 5) * 100;

  return (
    <div className="star-rating">
      <div className="star-visual" aria-label={`${score} out of 5 stars`}>
        <div className="star-base">★★★★★</div>
        <div
          className="star-fill"
          style={{ width: `${percentage}%` }}
        >
          ★★★★★
        </div>
      </div>

      <span className="star-score">{score.toFixed(1)}</span>
    </div>
  );
}

export default StarRating;