import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AssignmentFormDialog } from "@/components/assignment-form-dialog";

vi.mock("@/lib/assignment-service", () => ({
  createAssignment: vi.fn(),
  updateAssignment: vi.fn(),
}));

import { createAssignment } from "@/lib/assignment-service";

const createMock = createAssignment as unknown as ReturnType<typeof vi.fn>;

function renderDialog() {
  const onSuccess = vi.fn();
  render(
    <AssignmentFormDialog
      open
      onOpenChange={() => undefined}
      assignment={null}
      subjects={[]}
      onSuccess={onSuccess}
    />,
  );
  return { onSuccess };
}

async function fillTitle(title: string) {
  fireEvent.change(screen.getByPlaceholderText("Assignment title"), {
    target: { value: title },
  });
}

function submit() {
  fireEvent.click(screen.getByRole("button", { name: "Create" }));
}

function setEst(value: string) {
  const est = document.getElementById("estimated_study_time") as HTMLInputElement;
  fireEvent.change(est, { target: { value } });
}

describe("AssignmentFormDialog estimated study time", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createMock.mockResolvedValue({ id: "a1", title: "x" });
  });

  it("A. blank Est. Time submits with the value absent (null)", async () => {
    const { onSuccess } = renderDialog();
    await fillTitle("Blank est task");
    submit();
    await waitFor(() => {
      expect(createMock).toHaveBeenCalledTimes(1);
    });
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Blank est task", estimated_study_time: null }),
    );
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("B. 15 minutes succeeds", async () => {
    renderDialog();
    await fillTitle("Fifteen task");
    setEst("15");
    submit();
    await waitFor(() => {
      expect(createMock).toHaveBeenCalledTimes(1);
    });
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ estimated_study_time: 15 }),
    );
  });

  it("C. 1440 minutes succeeds", async () => {
    renderDialog();
    await fillTitle("Max est task");
    setEst("1440");
    submit();
    await waitFor(() => {
      expect(createMock).toHaveBeenCalledTimes(1);
    });
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ estimated_study_time: 1440 }),
    );
  });

  // Out-of-range values are rejected by native input validation
  // (min/max attributes) before React Hook Form ever runs, so the browser
  // itself shows the reason. These tests prove the submit is blocked and
  // no assignment is created.
  it.each([
    ["D. 0 is blocked", "0"],
    ["E. 1441 is blocked", "1441"],
  ])("%s", async (_label, value) => {
    renderDialog();
    await fillTitle("Bad est task");
    setEst(value);
    const est = document.getElementById("estimated_study_time") as HTMLInputElement;
    expect(est.validity.valid).toBe(false);
    submit();
    await new Promise((r) => setTimeout(r, 800));
    expect(createMock).not.toHaveBeenCalled();
  });

  it("F. non-numeric input sanitizes to blank and submits honestly", async () => {
    // Real browsers refuse non-numeric keystrokes in number inputs; forced
    // values sanitize to "" and must submit as absent — never as garbage.
    renderDialog();
    await fillTitle("Forced est task");
    setEst("abc");
    const est = document.getElementById("estimated_study_time") as HTMLInputElement;
    expect(est.value).toBe("");
    submit();
    await waitFor(() => {
      expect(createMock).toHaveBeenCalledTimes(1);
    });
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ estimated_study_time: null }),
    );
  });

  it("G. one submission creates exactly one assignment", async () => {
    renderDialog();
    await fillTitle("Exactly once task");
    submit();
    await waitFor(() => {
      expect(createMock).toHaveBeenCalledTimes(1);
    });
    expect(createMock.mock.calls).toHaveLength(1);
  });
});
