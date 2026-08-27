import pytest
from unittest.mock import patch, AsyncMock, call
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@pytest.mark.asyncio
async def test_scheduled_ingestion_and_processing_job_sequential(mocker):
    """
    A. Sequential execution: Prove ingest_all_feeds completes before process_pending_batch starts.
    """
    mock_db = mocker.patch("app.worker.get_database")

    mock_ingestion_cls = mocker.patch("app.worker.IngestionService")
    mock_ingestion_inst = mock_ingestion_cls.return_value

    # We will track execution order in a list
    execution_order = []

    async def mock_ingest(*args, **kwargs):
        execution_order.append("ingest_started")
        await asyncio.sleep(0.01)
        execution_order.append("ingest_finished")
        return mocker.Mock(feeds_attempted=1, feeds_succeeded=1, feeds_failed=0)

    async def mock_process(*args, **kwargs):
        execution_order.append("process_started")
        await asyncio.sleep(0.01)
        execution_order.append("process_finished")
        return {"processed_count": 5}

    mock_ingestion_inst.ingest_all_feeds = AsyncMock(side_effect=mock_ingest)
    mock_intelligence_process = mocker.patch("app.worker.intelligence_service.process_pending_batch", AsyncMock(side_effect=mock_process))

    from app.worker import scheduled_ingestion_and_processing_job
    await scheduled_ingestion_and_processing_job()

    # Assert sequential execution order
    assert execution_order == [
        "ingest_started",
        "ingest_finished",
        "process_started",
        "process_finished"
    ]

    mock_db.assert_called_once()
    mock_ingestion_inst.ingest_all_feeds.assert_called_once()
    mock_intelligence_process.assert_called_once_with(db=mock_db.return_value, limit=500)


def test_scheduler_configuration_and_lifecycle(mocker):
    """
    B. Scheduler configuration: Verify job configuration parameters
    D. Lifecycle: Verify start/stop semantics
    """
    mock_scheduler = mocker.patch("app.worker.scheduler")

    from app.worker import start_scheduler, stop_scheduler
    from app.worker import scheduled_ingestion_and_processing_job

    # Act
    start_scheduler()

    # Assert add_job args
    mock_scheduler.add_job.assert_called_once()
    call_args, call_kwargs = mock_scheduler.add_job.call_args

    assert call_args[0] == scheduled_ingestion_and_processing_job
    assert call_args[1] == "interval"
    assert call_kwargs["minutes"] == 15
    assert call_kwargs["id"] == "threat_atlas_ingestion_job"
    assert call_kwargs["max_instances"] == 1
    assert call_kwargs["replace_existing"] is True
    assert call_kwargs["misfire_grace_time"] == 300
    assert call_kwargs["coalesce"] is True

    # Verify it starts
    mock_scheduler.start.assert_called_once()

    # Act shutdown
    mock_scheduler.running = True
    stop_scheduler()

    # Verify shutdown
    mock_scheduler.shutdown.assert_called_once_with(wait=True)


@pytest.mark.asyncio
async def test_scheduled_job_handles_ingestion_failure(mocker, caplog):
    """
    C. Failure isolation: Verify failure in ingestion halts run but does not propagate
    """
    mocker.patch("app.worker.get_database")

    mock_ingestion_cls = mocker.patch("app.worker.IngestionService")
    mock_ingestion_inst = mock_ingestion_cls.return_value
    mock_ingestion_inst.ingest_all_feeds = AsyncMock(side_effect=Exception("Ingestion strictly failed"))

    mock_intelligence_process = mocker.patch("app.worker.intelligence_service.process_pending_batch", AsyncMock())

    from app.worker import scheduled_ingestion_and_processing_job

    # Call directly. It should NOT raise because of the try/except in the job
    await scheduled_ingestion_and_processing_job()

    # Intelligence processing should definitely not be invoked if ingestion failed
    mock_intelligence_process.assert_not_called()

    # Check that error was logged
    assert "Scheduled ingestion job failed: Ingestion strictly failed" in caplog.text
