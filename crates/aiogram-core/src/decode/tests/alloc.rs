//! A counting global allocator for the test binary: live bytes per thread, so tests that run
//! in parallel do not see each other's allocations (R04's "the batch buffer is freed").

use std::alloc::{GlobalAlloc, Layout, System};
use std::cell::Cell;

thread_local! {
    static LIVE: Cell<isize> = const { Cell::new(0) };
}

fn add(bytes: usize, sign: isize) {
    let bytes = isize::try_from(bytes).unwrap_or(isize::MAX);
    // `try_with`: the slot is gone while the thread exits
    let _ = LIVE.try_with(|live| live.set(live.get().wrapping_add(sign.wrapping_mul(bytes))));
}

struct Counting;

// SAFETY: every call is forwarded to `System` unchanged; only a thread-local counter is added.
unsafe impl GlobalAlloc for Counting {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        // SAFETY: same contract as the caller's
        let ptr = unsafe { System.alloc(layout) };
        if !ptr.is_null() {
            add(layout.size(), 1);
        }
        ptr
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        // SAFETY: same contract as the caller's
        unsafe { System.dealloc(ptr, layout) };
        add(layout.size(), -1);
    }
}

#[global_allocator]
static COUNTING: Counting = Counting;

/// Bytes allocated and not yet freed by this thread (frees of other threads' blocks included).
pub(crate) fn live() -> isize {
    LIVE.with(Cell::get)
}
