import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet-draw';
import type { AOI, JobResult, TargetResult } from '../api/client';

interface MapViewProps {
  selectedAOI: AOI | null;
  drawnGeometry: GeoJSON.Polygon | null;
  onGeometryDrawn: (g: GeoJSON.Polygon | null) => void;
  result: JobResult | null;
  visibleTargetKeys: Set<string>;
}

export function MapView({
  selectedAOI,
  drawnGeometry,
  onGeometryDrawn,
  result,
  visibleTargetKeys,
}: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const drawnLayerRef = useRef<L.FeatureGroup | null>(null);
  const aoiLayerRef = useRef<L.GeoJSON | null>(null);
  const overlaysRef = useRef<Map<string, L.ImageOverlay>>(new Map());

  useEffect(() => {
    if (mapRef.current) return;
    const map = L.map('map', {
      center: [29.9792, 31.1342],
      zoom: 13,
      attributionControl: true,
    });
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {
        maxZoom: 19,
        attribution: 'Tiles © Esri — World Imagery',
      },
    ).addTo(map);

    const drawn = new L.FeatureGroup();
    map.addLayer(drawn);
    drawnLayerRef.current = drawn;

    const drawControl = new L.Control.Draw({
      draw: {
        polygon: {
          shapeOptions: { color: '#f59e0b', weight: 2, fillOpacity: 0.1 },
          allowIntersection: false,
          showArea: true,
        },
        rectangle: {
          shapeOptions: { color: '#f59e0b', weight: 2, fillOpacity: 0.1 },
        },
        polyline: false,
        circle: false,
        marker: false,
        circlemarker: false,
      },
      edit: {
        featureGroup: drawn,
        remove: true,
      },
    });
    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, (e: L.LeafletEvent) => {
      const layer = (e as unknown as { layer: L.Layer }).layer;
      drawn.clearLayers();
      drawn.addLayer(layer);
      const geo = (layer as L.Polygon).toGeoJSON();
      onGeometryDrawn(geo.geometry as GeoJSON.Polygon);
    });
    map.on(L.Draw.Event.DELETED, () => {
      onGeometryDrawn(null);
    });
    map.on(L.Draw.Event.EDITED, () => {
      const layers = drawn.getLayers();
      if (layers.length > 0) {
        const geo = (layers[0] as L.Polygon).toGeoJSON();
        onGeometryDrawn(geo.geometry as GeoJSON.Polygon);
      }
    });

    mapRef.current = map;
  }, [onGeometryDrawn]);

  // Sync drawn layer when geometry is cleared externally
  useEffect(() => {
    if (!drawnGeometry && drawnLayerRef.current) {
      drawnLayerRef.current.clearLayers();
    }
  }, [drawnGeometry]);

  // Render the selected (saved) AOI on the map
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (aoiLayerRef.current) {
      map.removeLayer(aoiLayerRef.current);
      aoiLayerRef.current = null;
    }
    if (selectedAOI) {
      const layer = L.geoJSON(selectedAOI.geometry, {
        style: { color: '#fbbf24', weight: 2, fillOpacity: 0.05 },
      });
      layer.addTo(map);
      aoiLayerRef.current = layer;
      map.fitBounds(layer.getBounds(), { padding: [40, 40] });
    }
  }, [selectedAOI]);

  // Render heatmap overlays for visible targets
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove overlays for keys no longer visible
    overlaysRef.current.forEach((overlay, key) => {
      if (!result || !visibleTargetKeys.has(key)) {
        map.removeLayer(overlay);
        overlaysRef.current.delete(key);
      }
    });

    if (!result) return;
    const aoi = result.aoi;
    const [minX, minY, maxX, maxY] = aoi.bbox;
    const bounds = L.latLngBounds([
      [minY, minX],
      [maxY, maxX],
    ]);

    visibleTargetKeys.forEach((key) => {
      if (overlaysRef.current.has(key)) return;
      const target = result.targets[key] as TargetResult | undefined;
      if (!target?.heatmap_png) return;
      const overlay = L.imageOverlay(target.heatmap_png, bounds, { opacity: 0.85 });
      overlay.addTo(map);
      overlaysRef.current.set(key, overlay);
    });
  }, [result, visibleTargetKeys]);

  return <div id="map" />;
}
