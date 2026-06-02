import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const DEFAULT_DATA_PATH = "public/data/web_mock_restaurants.json";
const NAVER_ID_PATTERNS = [
  /\/restaurant\/(\d+)/,
  /\/place\/(\d+)/,
  /\/entry\/place\/(\d+)/,
  /[?&](?:placeId|entryId|id)=(\d+)/,
];
const BROWSER_USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36";
const GENERIC_NAVER_IMAGE_PATTERNS = [
  "static/maps/assets/images/og-map",
  "og-map-400x200",
];

function getArgValue(name, fallback) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) {
    return fallback;
  }
  return process.argv[index + 1];
}

function decodeHtml(value) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

function normalizeName(name) {
  return String(name || "")
    .replace(/\s+/g, "")
    .toLowerCase();
}

function extractNaverIdFromUrl(url) {
  for (const pattern of NAVER_ID_PATTERNS) {
    const match = String(url || "").match(pattern);
    if (match?.[1]) {
      return match[1];
    }
  }
  return "";
}

async function loadNaverUrlMap(filePath) {
  if (!filePath) {
    return { byId: new Map(), byName: new Map() };
  }

  const rawJson = await readFile(path.resolve(filePath), "utf-8");
  const rows = JSON.parse(rawJson.replace(/^\uFEFF/, ""));
  const byId = new Map();
  const byName = new Map();

  for (const row of rows) {
    const naverUrl = row.naver_url || row.naverUrl || row.naver_map_url || row.url || "";
    const naverId = String(row.naverID || row.naver_id || row.naver_place_id || extractNaverIdFromUrl(naverUrl));
    const nameKey = normalizeName(row.name);

    if (naverId && naverUrl) {
      byId.set(naverId, { naverId, naverUrl });
    }
    if (nameKey && naverUrl) {
      byName.set(nameKey, { naverId, naverUrl });
    }
  }

  return { byId, byName };
}

function mergeNaverUrl(restaurant, naverUrlMap) {
  const ownUrl = restaurant.naver_url || restaurant.naverUrl || restaurant.naver_map_url || restaurant.url || "";
  const ownId =
    restaurant.naverID ||
    restaurant.naver_id ||
    restaurant.naver_place_id ||
    restaurant.place_id ||
    extractNaverIdFromUrl(ownUrl) ||
    (/^\d+$/.test(String(restaurant.id)) ? String(restaurant.id) : "");

  const matchById = ownId ? naverUrlMap.byId.get(String(ownId)) : null;
  const matchByName = naverUrlMap.byName.get(normalizeName(restaurant.name));
  const matched = matchById || matchByName || null;

  if (!matched) {
    return restaurant;
  }

  return {
    ...restaurant,
    naver_place_id: matched.naverId || ownId,
    naver_url: matched.naverUrl,
    naver_map_url: matched.naverUrl,
  };
}

function getPlaceId(restaurant) {
  if (restaurant.naverID) return String(restaurant.naverID);
  if (restaurant.naver_id) return String(restaurant.naver_id);
  if (restaurant.naver_place_id) return String(restaurant.naver_place_id);
  if (restaurant.place_id) return String(restaurant.place_id);
  if (/^\d+$/.test(String(restaurant.id))) return String(restaurant.id);

  const url = restaurant.naver_url || restaurant.naverUrl || restaurant.naver_map_url || restaurant.url || "";
  return extractNaverIdFromUrl(url);
}

function getNaverMapUrl(restaurant) {
  const existingUrl = restaurant.naver_url || restaurant.naverUrl || restaurant.naver_map_url || restaurant.url || "";
  if (existingUrl) {
    return existingUrl;
  }

  const placeId = getPlaceId(restaurant);
  return placeId ? `https://map.naver.com/p/entry/place/${placeId}` : "";
}

function getThumbnailCandidateUrls(restaurant) {
  const placeId = getPlaceId(restaurant);
  const urls = [];
  const existingUrl = restaurant.naver_url || restaurant.naverUrl || restaurant.naver_map_url || restaurant.url || "";

  if (existingUrl) {
    urls.push(existingUrl);
    urls.push(existingUrl.replace(/\/review\/visitor.*$/, "/home"));
    urls.push(existingUrl.replace(/\/review\/visitor.*$/, "/photo"));
  }

  if (placeId) {
    urls.push(`https://m.place.naver.com/restaurant/${placeId}/home`);
    urls.push(`https://m.place.naver.com/restaurant/${placeId}/photo`);
    urls.push(`https://m.place.naver.com/restaurant/${placeId}/review/visitor?reviewSort=recent`);
    urls.push(`https://pcmap.place.naver.com/restaurant/${placeId}/home`);
    urls.push(`https://pcmap.place.naver.com/restaurant/${placeId}/photo`);
    urls.push(`https://pcmap.place.naver.com/place/${placeId}/home`);
    urls.push(`https://m.place.naver.com/place/${placeId}/home`);
  }

  const mapUrl = getNaverMapUrl(restaurant);
  if (mapUrl) {
    urls.push(mapUrl);
  }

  return [...new Set(urls)];
}

function isGenericNaverImage(url) {
  return GENERIC_NAVER_IMAGE_PATTERNS.some((pattern) => url.includes(pattern));
}

function extractMetaImage(html) {
  const patterns = [
    /<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["'][^>]*>/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["'][^>]*>/i,
    /<meta[^>]+name=["']twitter:image["'][^>]+content=["']([^"']+)["'][^>]*>/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+name=["']twitter:image["'][^>]*>/i,
  ];

  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match?.[1]) {
      return decodeHtml(match[1]);
    }
  }

  return "";
}

async function fetchThumbnailFromUrl(url) {
  const response = await fetch(url, {
    headers: {
      "User-Agent": BROWSER_USER_AGENT,
      "Accept": "text/html,application/xhtml+xml",
      "Referer": "https://m.place.naver.com/",
    },
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return extractMetaImage(await response.text());
}

async function fetchThumbnail(urls) {
  const errors = [];

  for (const url of urls) {
    try {
      const thumbnailUrl = await fetchThumbnailFromUrl(url);
      if (thumbnailUrl && !isGenericNaverImage(thumbnailUrl)) {
        return { thumbnailUrl, sourceUrl: url };
      }
      if (thumbnailUrl) {
        errors.push(`${url}: 네이버 기본 지도 이미지라 제외`);
      }
    } catch (error) {
      errors.push(`${url}: ${error.message}`);
    }
  }

  return { thumbnailUrl: "", sourceUrl: "", errors };
}

async function main() {
  const inputPath = path.resolve(getArgValue("--input", DEFAULT_DATA_PATH));
  const outputPath = path.resolve(getArgValue("--output", inputPath));
  const naverUrlDataPath = getArgValue("--naver-url-data", "");
  const rawJson = await readFile(inputPath, "utf-8");
  const restaurants = JSON.parse(rawJson.replace(/^\uFEFF/, ""));
  const naverUrlMap = await loadNaverUrlMap(naverUrlDataPath);

  const updated = [];
  for (const rawRestaurant of restaurants) {
    const restaurant = mergeNaverUrl(rawRestaurant, naverUrlMap);
    const naverUrl = getNaverMapUrl(restaurant);
    const thumbnailCandidateUrls = getThumbnailCandidateUrls(restaurant);

    if (thumbnailCandidateUrls.length === 0) {
      console.log(`[건너뜀] ${restaurant.name}: 네이버 플레이스 ID 또는 URL 없음`);
      updated.push(restaurant);
      continue;
    }

    const { thumbnailUrl, sourceUrl, errors = [] } = await fetchThumbnail(thumbnailCandidateUrls);
    if (!thumbnailUrl) {
      console.log(`[실패] ${restaurant.name}: 식당 대표 썸네일을 찾지 못함`);
      if (errors.length) {
        console.log(`  - ${errors.join("\n  - ")}`);
      }
      updated.push({ ...restaurant, naver_map_url: naverUrl });
      continue;
    }

    console.log(`[저장] ${restaurant.name}: ${sourceUrl}`);
    updated.push({
      ...restaurant,
      naver_map_url: naverUrl,
      thumbnail_url: thumbnailUrl,
    });
  }

  await writeFile(outputPath, `${JSON.stringify(updated, null, 2)}\n`, "utf-8");
  console.log(`완료: ${outputPath}`);
}

main();
