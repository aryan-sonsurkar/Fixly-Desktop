import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { MarkdownRenderer } from "@/components/ai/markdown-renderer";

describe("MarkdownRenderer input guard", () => {
  it("renders normal markdown", () => {
    const { container } = render(<MarkdownRenderer content="**Hello** world" />);
    expect(container.textContent).toContain("Hello");
  });

  it.each([[null], [undefined], [42], [{ text: "x" }], [["a"]] ])(
    "never throws on non-string content (%p)",
    (bad) => {
      expect(() =>
        render(<MarkdownRenderer content={bad as unknown as string} />),
      ).not.toThrow();
    },
  );
});
