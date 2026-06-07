import { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  HashRouter,
  Route,
  Routes,
  useLocation,
  useNavigationType
} from "react-router-dom";
import HomePage from "./pages/HomePage";
import ResultPage from "./pages/ResultPage";
import DetailPage from "./pages/DetailPage";
import "./App.css";

const getScrollKey = (location) =>
  `scroll-position:${location.pathname}${location.search}`;

const SCROLL_RESTORE_CLASS = "is-restoring-scroll";
const SCROLL_RESTORE_TIMEOUT = 900;

const saveScrollPosition = (location) => {
  sessionStorage.setItem(
    getScrollKey(location),
    JSON.stringify({
      x: window.scrollX,
      y: window.scrollY
    })
  );
};

const getSavedScrollPosition = (location) => {
  const savedPosition = sessionStorage.getItem(getScrollKey(location));
  if (!savedPosition) return null;

  try {
    return JSON.parse(savedPosition);
  } catch {
    return null;
  }
};

const restoreScrollPosition = ({ x = 0, y = 0 }, setIsRestoring) => {
  const targetX = Number(x) || 0;
  const targetY = Number(y) || 0;

  if (targetX === 0 && targetY === 0) {
    window.scrollTo(targetX, targetY);
    return undefined;
  }

  let frameId = null;
  let timeoutId = null;
  let isCancelled = false;

  const stopRestoring = () => {
    document.body.classList.remove(SCROLL_RESTORE_CLASS);
    setIsRestoring(false);
  };

  const finishRestoring = () => {
    if (isCancelled) return;

    isCancelled = true;
    if (frameId !== null) cancelAnimationFrame(frameId);
    if (timeoutId !== null) clearTimeout(timeoutId);
    window.scrollTo(targetX, targetY);
    stopRestoring();
  };

  const restoreUntilReady = () => {
    if (isCancelled) return;

    window.scrollTo(targetX, targetY);

    const maxScrollY = Math.max(
      0,
      document.documentElement.scrollHeight - window.innerHeight
    );
    const hasEnoughHeight = maxScrollY >= targetY - 2;
    const hasReachedTarget = Math.abs(window.scrollY - targetY) <= 2;

    if (hasEnoughHeight && hasReachedTarget) {
      finishRestoring();
      return;
    }

    frameId = requestAnimationFrame(restoreUntilReady);
  };

  setIsRestoring(true);
  document.body.classList.add(SCROLL_RESTORE_CLASS);
  frameId = requestAnimationFrame(restoreUntilReady);
  timeoutId = setTimeout(finishRestoring, SCROLL_RESTORE_TIMEOUT);

  return () => {
    isCancelled = true;
    if (frameId !== null) cancelAnimationFrame(frameId);
    if (timeoutId !== null) clearTimeout(timeoutId);
    stopRestoring();
  };
};

function ScrollPositionManager() {
  const location = useLocation();
  const navigationType = useNavigationType();
  const previousLocationRef = useRef(location);
  const currentLocationRef = useRef(location);
  const isRestoringRef = useRef(false);

  useEffect(() => {
    if (!("scrollRestoration" in window.history)) return undefined;

    const originalScrollRestoration = window.history.scrollRestoration;
    window.history.scrollRestoration = "manual";

    return () => {
      window.history.scrollRestoration = originalScrollRestoration;
    };
  }, []);

  useEffect(() => {
    let animationFrameId = null;

    const saveCurrentScrollPosition = () => {
      if (isRestoringRef.current) return;

      saveScrollPosition(currentLocationRef.current);
    };

    const scheduleSaveCurrentScrollPosition = () => {
      if (animationFrameId !== null) return;

      animationFrameId = requestAnimationFrame(() => {
        animationFrameId = null;
        saveCurrentScrollPosition();
      });
    };

    const handleKeyDown = (event) => {
      if (event.key === "Enter" || event.key === " ") {
        saveCurrentScrollPosition();
      }
    };

    window.addEventListener("scroll", scheduleSaveCurrentScrollPosition, {
      passive: true
    });
    window.addEventListener("beforeunload", saveCurrentScrollPosition);
    document.addEventListener("pointerdown", saveCurrentScrollPosition, true);
    document.addEventListener("keydown", handleKeyDown, true);

    return () => {
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId);
      }

      window.removeEventListener("scroll", scheduleSaveCurrentScrollPosition);
      window.removeEventListener("beforeunload", saveCurrentScrollPosition);
      document.removeEventListener("pointerdown", saveCurrentScrollPosition, true);
      document.removeEventListener("keydown", handleKeyDown, true);
    };
  }, []);

  useLayoutEffect(() => {
    const previousLocation = previousLocationRef.current;

    currentLocationRef.current = location;

    if (navigationType === "POP") {
      const savedPosition = getSavedScrollPosition(location);

      if (savedPosition) {
        previousLocationRef.current = location;
        return restoreScrollPosition(savedPosition, (isRestoring) => {
          isRestoringRef.current = isRestoring;
        });
      }
    } else if (previousLocation.pathname !== location.pathname) {
      window.scrollTo(0, 0);
    }

    previousLocationRef.current = location;
  }, [location, navigationType]);

  return null;
}

function ScrollToTopButton() {
  const location = useLocation();
  const [isVisible, setIsVisible] = useState(false);
  const isDetailPage = location.pathname.startsWith("/restaurants/");

  useEffect(() => {
    const updateVisibility = () => {
      setIsVisible(window.scrollY > 420);
    };

    updateVisibility();
    window.addEventListener("scroll", updateVisibility, { passive: true });

    return () => {
      window.removeEventListener("scroll", updateVisibility);
    };
  }, [location.pathname]);

  if (isDetailPage || !isVisible) {
    return null;
  }

  const handleScrollToTop = () => {
    const startY = window.scrollY;
    const duration = 280;
    const startTime = performance.now();

    const scrollStep = (currentTime) => {
      const progress = Math.min((currentTime - startTime) / duration, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 3);

      window.scrollTo(0, Math.round(startY * (1 - easedProgress)));

      if (progress < 1) {
        requestAnimationFrame(scrollStep);
      }
    };

    requestAnimationFrame(scrollStep);
  };

  return (
    <button
      className="scroll-top-button"
      onClick={handleScrollToTop}
      type="button"
      aria-label="맨 위로 이동"
    >
      <span className="scroll-top-label">맨 위로 이동</span>
      <span className="scroll-top-circle" aria-hidden="true" />
    </button>
  );
}

function App() {
  return (
    <HashRouter>
      <ScrollPositionManager />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/results" element={<ResultPage />} />
        <Route path="/restaurants/:id" element={<DetailPage />} />
      </Routes>
      <ScrollToTopButton />
    </HashRouter>
  );
}

export default App;
