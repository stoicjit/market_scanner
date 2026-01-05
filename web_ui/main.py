from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Load environment variables
load_dotenv()

app = FastAPI(title="Crypto Fakeout Scanner API", version="1.0.0")

# Templates and Static Files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_URL = os.getenv("DB_URL")

SYMBOLS = ["btcusdt", "ethusdt", "ltcusdt", "xrpusdt", "dogeusdt", "linkusdt", "adausdt"]
TIMEFRAMES = ["1h", "4h", "1d"]


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(DB_URL)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = None, fetchone: bool = False):
    """Execute a query and return results"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetchone:
                return dict(cur.fetchone()) if cur.rowcount > 0 else None
            return [dict(row) for row in cur.fetchall()]


@app.get("/api/status")
async def get_status():
    """System status and health check"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Test DB connection
                cur.execute("SELECT 1")
                
                # Get latest candle timestamps
                latest_candles = {}
                for symbol in SYMBOLS:
                    cur.execute(f'SELECT timestamp FROM "{symbol}_5m" ORDER BY id DESC LIMIT 1')
                    result = cur.fetchone()
                    if result:
                        latest_candles[symbol] = result[0].isoformat()
                
                return {
                    "status": "healthy",
                    "database": "connected",
                    "latest_candles": latest_candles,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System error: {str(e)}")


@app.get("/api/fakeouts")
async def get_fakeouts(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., btcusdt)"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe (1h, 4h, 1d)"),
    fakeout_type: Optional[str] = Query(None, description="Filter by type (high, low)"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get all fakeouts with optional filters"""
    try:
        # Build UNION query for all symbol/timeframe combinations
        union_queries = []
        
        for sym in SYMBOLS:
            # Apply symbol filter
            if symbol and sym != symbol.lower():
                continue
                
            for tf in TIMEFRAMES:
                # Apply timeframe filter
                if timeframe and tf != timeframe:
                    continue
                
                table_name = f'"{sym}_{tf}"'
                query = f"""
                    SELECT 
                        id,
                        timestamp,
                        open,
                        high,
                        low,
                        close,
                        volume,
                        rsi_8,
                        ema_20,
                        ema_50,
                        fakeout_type,
                        fakeout_level,
                        '{sym}' as symbol,
                        '{tf}' as timeframe
                    FROM {table_name}
                    WHERE is_fakeout = TRUE
                """
                
                # Apply type filter
                if fakeout_type:
                    query += f" AND fakeout_type = '{fakeout_type}'"
                
                union_queries.append(query)
        
        if not union_queries:
            return {"fakeouts": [], "total": 0}
        
        # Combine with UNION ALL
        full_query = " UNION ALL ".join(union_queries)
        full_query += f" ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
        
        fakeouts = execute_query(full_query)
        
        # Convert timestamps to ISO format
        for fakeout in fakeouts:
            if fakeout.get('timestamp'):
                fakeout['timestamp'] = fakeout['timestamp'].isoformat()
        
        return {
            "fakeouts": fakeouts,
            "total": len(fakeouts),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fakeouts: {str(e)}")


@app.get("/api/fakeouts/recent")
async def get_recent_fakeouts(limit: int = Query(10, description="Number of recent fakeouts")):
    """Get most recent fakeouts"""
    return await get_fakeouts(limit=limit)


@app.get("/api/fakeouts/{fakeout_id}")
async def get_fakeout_detail(fakeout_id: int, symbol: str, timeframe: str):
    """Get detailed information about a specific fakeout including context candles"""
    try:
        symbol = symbol.lower()
        table_name = f'"{symbol}_{timeframe}"'
        
        # Get the fakeout
        query = f"""
            SELECT 
                id, timestamp, open, high, low, close, volume,
                rsi_8, ema_20, ema_50, fakeout_type, fakeout_level,
                '{symbol}' as symbol, '{timeframe}' as timeframe
            FROM {table_name}
            WHERE id = %s AND is_fakeout = TRUE
        """
        
        fakeout = execute_query(query, (fakeout_id,), fetchone=True)
        
        if not fakeout:
            raise HTTPException(status_code=404, detail="Fakeout not found")
        
        fakeout_timestamp = fakeout['timestamp']
        
        # Get context candles based on timeframe
        context_candles = []
        
        if timeframe == "1h":
            # Get 5m candles: 1hr before and 2hr after
            context_table = f'"{symbol}_5m"'
            start_time = fakeout_timestamp - timedelta(hours=1)
            end_time = fakeout_timestamp + timedelta(hours=2)
            
            context_query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM {context_table}
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """
            context_candles = execute_query(context_query, (start_time, end_time))
            
        elif timeframe == "1d":
            # Get 1h candles: 24hr before and 24hr after
            context_table = f'"{symbol}_1h"'
            start_time = fakeout_timestamp - timedelta(hours=24)
            end_time = fakeout_timestamp + timedelta(hours=24)
            
            context_query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM {context_table}
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """
            context_candles = execute_query(context_query, (start_time, end_time))
        
        # Note: 4h fakeouts have no context by design
        
        # Convert timestamps
        fakeout['timestamp'] = fakeout['timestamp'].isoformat()
        for candle in context_candles:
            candle['timestamp'] = candle['timestamp'].isoformat()
        
        return {
            "fakeout": fakeout,
            "context_candles": context_candles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fakeout detail: {str(e)}")


@app.get("/api/fakeouts/stats")
async def get_fakeout_stats():
    """Get summary statistics for fakeouts"""
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Build queries for each time period
        stats = {
            "today": 0,
            "week": 0,
            "month": 0,
            "by_symbol": {},
            "by_timeframe": {}
        }
        
        # Initialize counters
        for symbol in SYMBOLS:
            stats["by_symbol"][symbol.upper()] = 0
        for tf in TIMEFRAMES:
            stats["by_timeframe"][tf] = 0
        
        # Query each table
        for symbol in SYMBOLS:
            for tf in TIMEFRAMES:
                table_name = f'"{symbol}_{tf}"'
                
                # Count by time period
                query = f"""
                    SELECT 
                        COUNT(*) FILTER (WHERE timestamp >= %s) as today,
                        COUNT(*) FILTER (WHERE timestamp >= %s) as week,
                        COUNT(*) FILTER (WHERE timestamp >= %s) as month,
                        COUNT(*) as total
                    FROM {table_name}
                    WHERE is_fakeout = TRUE
                """
                
                result = execute_query(query, (today_start, week_start, month_start), fetchone=True)
                
                if result:
                    stats["today"] += result["today"] or 0
                    stats["week"] += result["week"] or 0
                    stats["month"] += result["month"] or 0
                    
                    # Add to symbol and timeframe totals
                    total = result["total"] or 0
                    stats["by_symbol"][symbol.upper()] += total
                    stats["by_timeframe"][tf] += total
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


@app.get("/api/candles/{symbol}/{timeframe}")
async def get_candles(
    symbol: str,
    timeframe: str,
    limit: int = Query(100, description="Number of candles to return")
):
    """Get OHLCV candles for a symbol/timeframe"""
    try:
        symbol = symbol.lower()
        if symbol not in SYMBOLS:
            raise HTTPException(status_code=400, detail="Invalid symbol")
        if timeframe not in ["5m", "1h", "4h", "1d", "1w", "1M"]:
            raise HTTPException(status_code=400, detail="Invalid timeframe")
        
        table_name = f'"{symbol}_{timeframe}"'
        
        query = f"""
            SELECT timestamp, open, high, low, close, volume, rsi_8, ema_20, ema_50
            FROM {table_name}
            ORDER BY id DESC
            LIMIT %s
        """
        
        candles = execute_query(query, (limit,))
        
        # Reverse to chronological order
        candles.reverse()
        
        # Convert timestamps
        for candle in candles:
            candle['timestamp'] = candle['timestamp'].isoformat()
        
        return {"symbol": symbol, "timeframe": timeframe, "candles": candles}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candles: {str(e)}")


@app.get("/api/candles/{symbol}/{timeframe}/latest")
async def get_latest_candle(symbol: str, timeframe: str):
    """Get the latest candle for a symbol/timeframe"""
    try:
        symbol = symbol.lower()
        table_name = f'"{symbol}_{timeframe}"'
        
        query = f"""
            SELECT timestamp, open, high, low, close, volume, rsi_8, ema_20, ema_50
            FROM {table_name}
            ORDER BY id DESC
            LIMIT 1
        """
        
        candle = execute_query(query, fetchone=True)
        
        if not candle:
            raise HTTPException(status_code=404, detail="No candles found")
        
        candle['timestamp'] = candle['timestamp'].isoformat()
        
        return {"symbol": symbol, "timeframe": timeframe, "candle": candle}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching latest candle: {str(e)}")


@app.get("/api/levels/{symbol}")
async def get_levels(symbol: str, timeframe: Optional[str] = Query(None, description="daily, weekly, or monthly")):
    """Get filtered high and low levels for a symbol"""
    try:
        symbol = symbol.lower()
        if symbol not in SYMBOLS:
            raise HTTPException(status_code=400, detail="Invalid symbol")
        
        # Query high levels
        high_query = """
            SELECT level, timestamp, timeframe
            FROM "high_levels"
            WHERE symbol = %s
        """
        params = [symbol]
        
        if timeframe:
            high_query += " AND timeframe = %s"
            params.append(timeframe)
        
        high_query += " ORDER BY timestamp DESC"
        
        high_levels = execute_query(high_query, tuple(params))
        
        # Query low levels
        low_query = """
            SELECT level, timestamp, timeframe
            FROM "low_levels"
            WHERE symbol = %s
        """
        params = [symbol]
        
        if timeframe:
            low_query += " AND timeframe = %s"
            params.append(timeframe)
        
        low_query += " ORDER BY timestamp DESC"
        
        low_levels = execute_query(low_query, tuple(params))
        
        # Convert timestamps
        for level in high_levels:
            level['timestamp'] = level['timestamp'].isoformat()
        for level in low_levels:
            level['timestamp'] = level['timestamp'].isoformat()
        
        return {
            "symbol": symbol,
            "high_levels": high_levels,
            "low_levels": low_levels
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching levels: {str(e)}")


@app.get("/api/levels/all")
async def get_all_levels():
    """Get all levels for all symbols"""
    try:
        all_levels = {}
        
        for symbol in SYMBOLS:
            result = await get_levels(symbol)
            all_levels[symbol.upper()] = {
                "high_levels": result["high_levels"],
                "low_levels": result["low_levels"]
            }
        
        return all_levels
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all levels: {str(e)}")


@app.get("/api/db/stats")
async def get_db_stats():
    """Get database statistics (table sizes, record counts)"""
    try:
        stats = {}
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for symbol in SYMBOLS:
                    stats[symbol.upper()] = {}
                    for tf in ["5m", "1h", "4h", "1d", "1w", "1M"]:
                        table_name = f'"{symbol}_{tf}"'
                        
                        # Get count
                        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                        count = cur.fetchone()["count"]
                        
                        # Get fakeout count
                        cur.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE is_fakeout = TRUE")
                        fakeout_count = cur.fetchone()["count"]
                        
                        stats[symbol.upper()][tf] = {
                            "total_candles": count,
                            "fakeouts": fakeout_count
                        }
                
                # Get level counts
                cur.execute('SELECT COUNT(*) as count FROM "high_levels"')
                high_level_count = cur.fetchone()["count"]
                
                cur.execute('SELECT COUNT(*) as count FROM "low_levels"')
                low_level_count = cur.fetchone()["count"]
                
                stats["levels"] = {
                    "high_levels": high_level_count,
                    "low_levels": low_level_count
                }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching DB stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Serve the SPA (MUST BE LAST - catch-all route)
@app.get("/", response_class=HTMLResponse)
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(request: Request, full_path: str = ""):
    """Serve the single-page application for all non-API routes"""
    return templates.TemplateResponse("index.html", {"request": request})