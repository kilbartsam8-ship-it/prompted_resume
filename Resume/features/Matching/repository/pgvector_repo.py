import asyncpg
import numpy as np
from typing import AsyncIterator, Tuple
from Resume.features.Matching.exception import RepositoryError


class PgVectorRepository:
    def __init__(self, dsn: str, batch_size: int = 500):
        self.dsn = dsn
        self.batch_size = batch_size
        self._pool: asyncpg.Pool | None = None

    async def init(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(dsn=self.dsn)

    async def close(self):
        if self._pool:
            await self._pool.close()

    async def fetch_jd_embeddings(
        self,
    ) -> AsyncIterator[Tuple[int, np.ndarray]]:
        """
        Stream JD embeddings in batches.
        Avoids loading everything into memory.
        """
        if not self._pool:
            raise RepositoryError("Pool not initialized")

        try:
            async with self._pool.acquire() as conn:
                stmt = await conn.prepare("""
                    SELECT id, embedding
                    FROM job_descriptions
                    WHERE is_active = true
                """)

                async for record in stmt.cursor():
                    emb = np.asarray(record["embedding"], dtype=np.float32)
                    yield record["id"], emb

        except Exception as e:
            raise RepositoryError(f"JD embedding fetch failed: {e}")
