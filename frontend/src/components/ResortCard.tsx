import { useState } from "react";
import { Resort, Camera } from "@/types";
import { calcAverages } from "@/lib/calc-averages";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Medal, ChevronDown, ChevronUp, MapPin, Globe } from "lucide-react";

const resortMapsUrls: Record<string, string> = {
  stevens_pass: "https://maps.app.goo.gl/QGEX4scWkhDeL8o59",
  crystal_mountain: "https://maps.app.goo.gl/47PTW6cnDW3a782C8",
  summit_snoqualmie: "https://maps.app.goo.gl/5fZ6gqg29B5qdtiU6",
  mt_baker: "https://maps.app.goo.gl/Gtx5hkUMuZB9Bzkd9",
  mission_ridge: "https://maps.app.goo.gl/j1P7FuwrPSUozNWe7",
  white_pass: "https://maps.app.goo.gl/CiFRKHwtpGUBNEJe8",
  schweitzer: "https://maps.app.goo.gl/Y2LWQrhNk59SSzfC6",
  mt_hood_meadows: "https://maps.app.goo.gl/yTZH5ST8Q6euzybh8",
  whistler_blackcomb: "https://maps.app.goo.gl/9Njw9Q16wVVCqHFN8",
  "49_degrees_north": "https://maps.app.goo.gl/xqNuPVdGmS4jeFX17",
  big_white: "https://maps.app.goo.gl/VDrcCU8KW7qminie9",
};

const resortWebsiteUrls: Record<string, string> = {
  stevens_pass: "https://www.stevenspass.com/",
  crystal_mountain: "https://www.crystalmountainresort.com/",
  summit_snoqualmie: "https://www.summitatsnoqualmie.com/",
  mt_baker: "https://www.mtbaker.us/",
  mission_ridge: "https://www.missionridge.com/",
  white_pass: "https://skiwhitepass.com/",
  schweitzer: "https://www.schweitzer.com/",
  mt_hood_meadows: "https://www.skihood.com/",
  whistler_blackcomb: "https://www.whistlerblackcomb.com/",
  "49_degrees_north": "https://ski49n.com/",
  big_white: "https://www.bigwhite.com/",
};

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
        <Medal className="h-6 w-6" />
        <span className="font-bold">#1</span>
      </div>
    );
  }
  if (rank === 2) {
    return (
      <div className="flex items-center gap-1 text-gray-400">
        <Medal className="h-6 w-6" />
        <span className="font-bold">#2</span>
      </div>
    );
  }
  if (rank === 3) {
    return (
      <div className="flex items-center gap-1 text-amber-700">
        <Medal className="h-6 w-6" />
        <span className="font-bold">#3</span>
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
  const mapsUrl = resortMapsUrls[resort.resort_key];
  const websiteUrl = resortWebsiteUrls[resort.resort_key];

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
            {websiteUrl && (
              <a
                href={websiteUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="p-1 rounded hover:bg-gray-100"
                title="Visit resort website"
              >
                <Globe className="h-5 w-5 text-muted-foreground hover:text-primary" />
              </a>
            )}
            {mapsUrl && (
              <a
                href={mapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="p-1 rounded hover:bg-gray-100"
                title="Open in Google Maps"
              >
                <MapPin className="h-5 w-5 text-muted-foreground hover:text-primary" />
              </a>
            )}
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
        <div className="mt-2 text-sm text-muted-foreground">
          {successfulCameras}/{resort.cameras.length} cameras analyzed
          <span className="ml-2 text-primary">
            {expanded ? "Click to collapse" : "Click for details"}
          </span>
        </div>

        {expanded && (
          <div className="mt-6 space-y-6">
            <div>
              <h3 className="font-semibold text-lg border-b pb-2 mb-4">Scores</h3>
              <div className="text-center mb-6">
                <div className={`text-4xl font-bold ${getScoreColor(avg.composite)}`}>
                  {avg.composite.toFixed(1)}
                </div>
                <div className="text-sm text-muted-foreground">Overall</div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.entries(avg)
                  .filter(([key]) => key !== "composite" && key !== "snow_depth_inches")
                  .map(([key, value]) => (
                    <div key={key} className="text-center">
                      <div className={`text-xl font-bold ${getScoreColor(value)}`}>
                        {value.toFixed(1)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {formatLabel(key)}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-lg border-b pb-2">Cameras</h3>
              {resort.cameras.map((camera, index) => (
                <CameraCard key={index} camera={camera} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
