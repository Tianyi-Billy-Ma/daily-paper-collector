from unittest.mock import AsyncMock, MagicMock

import pytest

from src.pipeline import DailyPipeline


@pytest.mark.asyncio
async def test_daily_run_embeds_only_papers_inserted_by_current_run() -> None:
    fetched_papers = [{"arxiv_id": "new"}, {"arxiv_id": "duplicate"}]
    new_papers = [{"id": 1, "arxiv_id": "new"}]
    pipeline = DailyPipeline.__new__(DailyPipeline)
    pipeline.fetcher = MagicMock()
    pipeline.fetcher.fetch_today = AsyncMock(return_value=fetched_papers)
    pipeline.store = MagicMock()
    pipeline.store.save_papers.return_value = new_papers
    pipeline.embedder = MagicMock()
    pipeline.interest_mgr = MagicMock()
    pipeline.interest_mgr.get_interests_with_embeddings.return_value = []
    pipeline.report_gen = MagicMock()
    pipeline.report_gen.generate_general = AsyncMock(return_value="report")
    pipeline.chinese_enabled = False
    pipeline.logger = MagicMock()

    await pipeline.run()

    pipeline.embedder.compute_embeddings.assert_called_once_with(new_papers, pipeline.store)
