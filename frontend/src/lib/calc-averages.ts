import { Camera } from "@/types";

export interface Averages {
  [key: string]: number;
}

export function calcAverages(cameras: Camera[]): Averages {
  const ratings = cameras
    .filter((c) => c.rating !== null && c.rating !== undefined)
    .map((c) => c.rating!);

  if (ratings.length === 0) {
    return { composite: 0 };
  }

  // Collect all numeric values by field name
  const fieldValues: Record<string, number[]> = {};

  for (const rating of ratings) {
    // Add confidence
    if (rating.confidence != null) {
      if (!fieldValues["confidence"]) fieldValues["confidence"] = [];
      fieldValues["confidence"].push(rating.confidence);
    }

    // Add category values (safely handle missing categories)
    const categories = rating.categories || {};
    for (const [key, value] of Object.entries(categories)) {
      if (typeof value === "number" && value != null) {
        if (!fieldValues[key]) fieldValues[key] = [];
        fieldValues[key].push(value);
      }
    }
  }

  // Calculate averages
  const avg: Averages = {};
  for (const [field, vals] of Object.entries(fieldValues)) {
    avg[field] = vals.reduce((a, b) => a + b, 0) / vals.length;
  }

  // Composite is average of all category scores (excluding snow_depth_inches)
  const categoryScores = Object.entries(avg)
    .filter(([k]) => k !== "snow_depth_inches")
    .map(([, v]) => v);

  avg.composite =
    categoryScores.length > 0
      ? categoryScores.reduce((a, b) => a + b, 0) / categoryScores.length
      : 0;

  return avg;
}
