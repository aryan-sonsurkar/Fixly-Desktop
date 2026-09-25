import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  splitExtension,
  prettifyStem,
  formatDisplayName,
  DocumentFilename,
} from "@/components/documents/document-filename";

describe("splitExtension", () => {
  it("splits a normal name", () => {
    expect(splitExtension("resume.pdf")).toEqual({ stem: "resume", ext: ".pdf" });
  });

  it("collapses a duplicated trailing extension", () => {
    expect(splitExtension("Aryan_Sonsurkar_Software_Developer_Resume.pdf.pdf")).toEqual({
      stem: "Aryan_Sonsurkar_Software_Developer_Resume",
      ext: ".pdf",
    });
  });

  it("collapses case-insensitive duplicates", () => {
    expect(splitExtension("notes.PDF.pdf")).toEqual({ stem: "notes", ext: ".pdf" });
  });

  it("keeps multi-dot stems", () => {
    expect(splitExtension("report.final.pdf")).toEqual({ stem: "report.final", ext: ".pdf" });
  });

  it("handles missing extension", () => {
    expect(splitExtension("README")).toEqual({ stem: "README", ext: "" });
  });

  it("handles dotfiles and trailing dots", () => {
    expect(splitExtension(".env")).toEqual({ stem: ".env", ext: "" });
    expect(splitExtension("name.")).toEqual({ stem: "name.", ext: "" });
  });

  it("handles image extensions", () => {
    expect(splitExtension("image.png")).toEqual({ stem: "image", ext: ".png" });
  });
});

describe("prettifyStem", () => {
  it("replaces underscores and collapses whitespace", () => {
    expect(prettifyStem("Aryan_Sonsurkar__Resume")).toBe("Aryan Sonsurkar Resume");
  });

  it("leaves spaced names alone", () => {
    expect(prettifyStem("DBMS Notes")).toBe("DBMS Notes");
  });
});

describe("formatDisplayName", () => {
  it("never duplicates the extension", () => {
    expect(formatDisplayName("resume.pdf")).toBe("resume.pdf");
    expect(formatDisplayName("Aryan_Sonsurkar_Software_Developer_Resume.pdf.pdf")).toBe(
      "Aryan Sonsurkar Software Developer Resume.pdf",
    );
    expect(formatDisplayName("DBMS_Notes.pdf")).toBe("DBMS Notes.pdf");
    expect(formatDisplayName("report.final.pdf")).toBe("report.final.pdf");
  });
});

describe("DocumentFilename", () => {
  it("renders prettified name once with full original in tooltip", () => {
    const { container } = render(
      <DocumentFilename name="Aryan_Sonsurkar_Software_Developer_Resume.pdf.pdf" />,
    );
    const outer = container.firstChild as HTMLElement;
    expect(outer.getAttribute("title")).toBe("Aryan_Sonsurkar_Software_Developer_Resume.pdf.pdf");
    expect(screen.getByText("Aryan Sonsurkar Software Developer Resume")).toBeTruthy();
    expect(screen.getByText(".pdf")).toBeTruthy();
    expect(container.textContent).not.toContain(".pdf.pdf");
  });

  it("keeps the extension visible as its own unit", () => {
    render(<DocumentFilename name="Very_Long_DBMS_Assignment_Notes_For_Semester_Three_Final_Version.pdf" />);
    expect(screen.getByText(".pdf")).toBeTruthy();
  });
});
