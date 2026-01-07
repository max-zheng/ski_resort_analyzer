import { useState } from "react";
import { Resort, Camera } from "@/types";
import { calcAverages } from "@/lib/calc-averages";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, Medal, ChevronDown, ChevronUp } from "lucide-react";

interface ResortCardProps {
  resort: Resort;
  rank: number;
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getScoreColor(score: number): string {
  if (score >= 8) return "text-green-600";
  if (score >= 6) return "text-blue-600";
  if (score >= 4) return "text-yellow-600";
  return "text-red-600";
}

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <div className="flex items-center gap-1 text-yellow-500">
        <Trophy className="h-6 w-6" />
        <span className="font-bold">#1</span>
      </div>
    );
  }
  if (rank <= 3) {
    return (
      <div className="flex items-center gap-1 text-gray-500">
        <Medal className="h-5 w-5" />
        <span className="font-semibold">#{rank}</span>
      </div>
    );
  }
  return <span className="text-muted-foreground font-medium">#{rank}</span>;
}

function CameraCard({ camera }: { camera: Camera }) {
  const rating = camera.rating;
  const categories = rating?.categories || {};

  const imageUrl = camera.is_base64
    ? `data:image/jpeg;base64,${camera.image_url}`
    : camera.image_url;

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <div className="flex flex-col md:flex-row gap-4">
        {imageUrl && (
          <div className="md:w-1/2">
            <img
              src={imageUrl}
              alt={camera.camera_name}
              className="w-full rounded-lg object-cover"
            />
          </div>
        )}
        <div className="md:w-1/2">
          <h4 className="font-semibold text-lg mb-2">{camera.camera_name}</h4>
          {rating ? (
            <>
              <div className="grid grid-cols-2 gap-2 mb-3">
                {Object.entries(categories).map(([key, value]) => (
                  <div key={key} className="text-sm">
                    <span className="text-muted-foreground">{formatLabel(key)}:</span>{" "}
                    <span className={`font-semibold ${typeof value === 'number' ? getScoreColor(value) : ''}`}>
                      {key === "snow_depth_inches" ? `${value}"` : `${value}/10`}
                    </span>
                  </div>
                ))}
              </div>
              <div className="text-sm">
                <span className="text-muted-foreground">Confidence:</span>{" "}
                <span className={`font-semibold ${getScoreColor(rating.confidence)}`}>
                  {rating.confidence}/10
                </span>
              </div>
              {rating.notes && (
                <p className="text-sm text-muted-foreground mt-2 italic">
                  "{rating.notes}"
                </p>
              )}
            </>
          ) : camera.error ? (
            <p className="text-red-500 text-sm">Error: {camera.error}</p>
          ) : (
            <p className="text-muted-foreground text-sm">No rating available</p>
          )}
        </div>
      </div>
    </div>
  );
}

export function ResortCard({ resort, rank }: ResortCardProps) {
  const [expanded, setExpanded] = useState(false);
  const avg = calcAverages(resort.cameras);
  const successfulCameras = resort.cameras.filter((c) => c.rating !== null).length;

  return (
    <Card
      className="hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <RankBadge rank={rank} />
            <CardTitle className="text-xl">{resort.resort_name}</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={avg.composite >= 7 ? "success" : "secondary"} className="text-lg px-3 py-1">
              {avg.composite.toFixed(1)}/10
            </Badge>
            {expanded ? (
              <ChevronUp className="h-5 w-5 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          {Object.entries(avg)
            .filter(([key]) => key !== "composite" && key !== "snow_depth_inches")
            .map(([key, value]) => (
              <div key={key} className="text-center">
                <div className={`text-2xl font-bold ${getScoreColor(value)}`}>
                  {value.toFixed(1)}
                </div>
                <div className="text-sm text-muted-foreground">
                  {formatLabel(key)}
                </div>
              </div>
            ))}
        </div>
        <div className="mt-4 text-sm text-muted-foreground">
          {successfulCameras}/{resort.cameras.length} cameras analyzed
          <span className="ml-2 text-primary">
            {expanded ? "Click to collapse" : "Click to see cameras"}
          </span>
        </div>

        {expanded && (
          <div className="mt-6 space-y-4">
            <h3 className="font-semibold text-lg border-b pb-2">Camera Details</h3>
            {resort.cameras.map((camera, index) => (
              <CameraCard key={index} camera={camera} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
