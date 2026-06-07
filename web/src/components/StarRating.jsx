function StarRating({ score }) {
  /* visualise star ratings
  floor rating data in 0.5 intervals & display stars
  user still sees original data, not floored
  */
  const rawScore = Number(score);

  const numericScore = Number.isFinite(rawScore) ? Math.max(rawScore, 0) : 0;
  const percentage = (numericScore / 5) * 100;
  const formattedScore = rawScore === -1 ? "?" : numericScore.toFixed(1);

  return (
    <div className="star-rating">
      <div className="star-visual" aria-label={`${formattedScore} out of 5 stars`}>
        <div className="star-base">★★★★★</div>
        <div
          className="star-fill"
          style={{ width: `${percentage}%` }}
        >
          ★★★★★
        </div>
      </div>

      <span className="star-score">{formattedScore}</span>
    </div>
  );
}

export default StarRating;