import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from command_line_assistant.dbus.sender_context import (
    get_current_sender,
    sender_context,
)


class TestSenderContext:
    """Test suite for sender_context thread-local context manager."""

    def test_basic_functionality(self):
        """Test basic sender context functionality."""
        # Initially no sender should be set
        assert get_current_sender() == ""

        # Set sender using context manager
        with sender_context("test_sender"):
            assert get_current_sender() == "test_sender"

        # After context exits, sender should be cleared
        assert get_current_sender() == ""

    def test_nested_contexts(self):
        """Test that nested context managers work correctly."""
        assert get_current_sender() == ""

        with sender_context("outer_sender"):
            assert get_current_sender() == "outer_sender"

            with sender_context("inner_sender"):
                assert get_current_sender() == "inner_sender"

            # Should restore to outer sender
            assert get_current_sender() == "outer_sender"

        # Should be cleared after all contexts exit
        assert get_current_sender() == ""

    def test_exception_handling(self):
        """Test that exceptions don't corrupt thread-local state."""
        assert get_current_sender() == ""

        # Set initial context
        with sender_context("initial_sender"):
            assert get_current_sender() == "initial_sender"

            try:
                with sender_context("exception_sender"):
                    assert get_current_sender() == "exception_sender"
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # Should restore to initial sender after exception
            assert get_current_sender() == "initial_sender"

        # Should be cleared after all contexts exit
        assert get_current_sender() == ""

    def test_thread_isolation(self):
        """Test that different threads have isolated sender contexts."""
        results = {}
        barrier = threading.Barrier(2)

        def thread_function(thread_id, sender_name):
            """Function to run in separate thread."""
            # Verify no initial sender
            results[f"{thread_id}_initial"] = get_current_sender()

            # Set sender in this thread
            with sender_context(sender_name):
                # Wait for both threads to set their contexts
                barrier.wait()

                # Verify this thread's sender is correct
                results[f"{thread_id}_during"] = get_current_sender()

                # Sleep briefly to allow other thread to potentially interfere
                time.sleep(0.1)

                # Verify sender is still correct after sleep
                results[f"{thread_id}_after_sleep"] = get_current_sender()

            # Verify sender is cleared after context
            results[f"{thread_id}_final"] = get_current_sender()

        # Create and start threads
        thread1 = threading.Thread(target=thread_function, args=(1, "sender_1"))
        thread2 = threading.Thread(target=thread_function, args=(2, "sender_2"))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Verify thread isolation
        assert results["1_initial"] == ""
        assert results["2_initial"] == ""
        assert results["1_during"] == "sender_1"
        assert results["2_during"] == "sender_2"
        assert results["1_after_sleep"] == "sender_1"
        assert results["2_after_sleep"] == "sender_2"
        assert results["1_final"] == ""
        assert results["2_final"] == ""

    def test_concurrent_threads_stress_test(self):
        """Test many concurrent threads don't interfere with each other."""
        num_threads = 10
        iterations_per_thread = 5
        results = {}

        def worker_thread(thread_id):
            """Worker function for stress testing."""
            thread_results = []
            sender_name = f"sender_{thread_id}"

            for _iteration in range(iterations_per_thread):
                # Verify no initial sender
                thread_results.append(("initial", get_current_sender()))

                with sender_context(sender_name):
                    # Verify correct sender
                    thread_results.append(("during", get_current_sender()))

                    # Add some variability in timing
                    time.sleep(0.01 * (thread_id % 3))

                    # Verify sender still correct
                    thread_results.append(("after_sleep", get_current_sender()))

                # Verify sender cleared
                thread_results.append(("final", get_current_sender()))

            results[thread_id] = thread_results

        # Run threads concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]

            # Wait for all threads to complete
            for future in as_completed(futures):
                future.result()  # This will raise any exceptions that occurred

        # Verify all results
        for thread_id in range(num_threads):
            thread_results = results[thread_id]
            sender_name = f"sender_{thread_id}"

            for iteration in range(iterations_per_thread):
                base_idx = iteration * 4
                assert thread_results[base_idx] == ("initial", "")
                assert thread_results[base_idx + 1] == ("during", sender_name)
                assert thread_results[base_idx + 2] == ("after_sleep", sender_name)
                assert thread_results[base_idx + 3] == ("final", "")

    def test_main_thread_isolation(self):
        """Test that main thread context is isolated from worker threads."""
        main_thread_sender = None
        worker_thread_sender = None

        # Set sender in main thread
        with sender_context("main_sender"):
            main_thread_sender = get_current_sender()

            def worker():
                nonlocal worker_thread_sender
                # Worker thread should not see main thread's sender
                worker_thread_sender = get_current_sender()

                # Set different sender in worker thread
                with sender_context("worker_sender"):
                    pass  # This shouldn't affect main thread

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join()

            # Main thread sender should be unchanged
            assert get_current_sender() == "main_sender"

        # Verify isolation
        assert main_thread_sender == "main_sender"
        assert worker_thread_sender == ""

    def test_thread_local_cleanup(self):
        """Test that thread-local data is properly cleaned up."""
        cleanup_results = {}

        def worker(thread_id):
            """Worker that sets context and records cleanup."""
            with sender_context(f"sender_{thread_id}"):
                # Context is active
                cleanup_results[f"{thread_id}_active"] = get_current_sender()

            # Context should be cleaned up
            cleanup_results[f"{thread_id}_cleaned"] = get_current_sender()

        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify cleanup
        for i in range(5):
            assert cleanup_results[f"{i}_active"] == f"sender_{i}"
            assert cleanup_results[f"{i}_cleaned"] == ""

    def test_delattr_error_handling(self):
        """Test handling of delattr when attribute doesn't exist."""
        # This tests the edge case where delattr might be called on non-existent attribute
        assert get_current_sender() == ""

        with sender_context("test"):
            assert get_current_sender() == "test"

        # Should handle delattr gracefully even if attribute doesn't exist
        assert get_current_sender() == ""

        # Test with nested contexts where inner context might not exist
        with sender_context("outer"):
            with sender_context("inner"):
                pass
            assert get_current_sender() == "outer"
        with sender_context("outer"):
            with sender_context("inner"):
                pass
            assert get_current_sender() == "outer"
