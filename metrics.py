"""Metrics and monitoring for the application."""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
import json


class MetricsCollector:
    """Collect and track application metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = defaultdict(list)
        self.start_time = time.time()
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self.counters[name] += value
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric."""
        self.gauges[name] = value
    
    def record_histogram(self, name: str, value: float) -> None:
        """Record a histogram value."""
        self.histograms[name].append(value)
    
    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self.counters.get(name, 0)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get gauge value."""
        return self.gauges.get(name)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        uptime = time.time() - self.start_time
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "counters": dict(self.counters),
            "gauges": self.gauges,
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self.histograms
            }
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.start_time = time.time()


class PerformanceTimer:
    """Context manager for performance timing."""
    
    def __init__(self, name: str, metrics: MetricsCollector = None):
        """Initialize timer."""
        self.name = name
        self.metrics = metrics
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record metric."""
        self.duration = time.time() - self.start_time
        
        if self.metrics:
            self.metrics.record_histogram(f"{self.name}_duration", self.duration)
            if exc_type is None:
                self.metrics.increment_counter(f"{self.name}_success")
            else:
                self.metrics.increment_counter(f"{self.name}_error")


# Global metrics instance
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics instance."""
    return _metrics


def record_articles_fetched(site: str, count: int) -> None:
    """Record articles fetched from a site."""
    _metrics.increment_counter("articles_fetched_total", count)
    _metrics.increment_counter(f"articles_fetched_{site}", count)


def record_fetch_duration(site: str, duration: float) -> None:
    """Record fetch duration for a site."""
    _metrics.record_histogram("fetch_duration_seconds", duration)
    _metrics.record_histogram(f"fetch_duration_{site}", duration)


def record_error(error_type: str) -> None:
    """Record an error."""
    _metrics.increment_counter("errors_total")
    _metrics.increment_counter(f"errors_{error_type}")


def set_cache_size(size: int) -> None:
    """Set cache size metric."""
    _metrics.set_gauge("cache_size_articles", size)


def set_sites_count(count: int) -> None:
    """Set configured sites count."""
    _metrics.set_gauge("sites_configured", count)


def set_sites_with_articles(count: int) -> None:
    """Set sites with articles count."""
    _metrics.set_gauge("sites_with_articles", count)


def get_metrics_summary() -> str:
    """Get human-readable metrics summary."""
    metrics = _metrics.get_all_metrics()
    
    summary = f"""
=== APPLICATION METRICS ===
Timestamp: {metrics['timestamp']}
Uptime: {metrics['uptime_seconds']:.1f}s

COUNTERS:
"""
    for name, value in metrics['counters'].items():
        summary += f"  {name}: {value}\n"
    
    summary += "\nGAUGES:\n"
    for name, value in metrics['gauges'].items():
        summary += f"  {name}: {value}\n"
    
    summary += "\nHISTOGRAMS:\n"
    for name, stats in metrics['histograms'].items():
        if stats:
            summary += f"  {name}: avg={stats['avg']:.2f}s, min={stats['min']:.2f}s, max={stats['max']:.2f}s\n"
    
    return summary
