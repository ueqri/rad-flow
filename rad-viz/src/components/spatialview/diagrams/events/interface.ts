export const DEFAULT_URL = "https://embed.diagrams.net/" as const;
export const MESSAGE_EVENT = "message" as const;

export type Config = {
  url?: string;
  compress?: boolean;
  data?: string;
  format?: "xml" /*not supported by diagrams currently*/ | "xmlsvg";
  title?: string;
  onInit?: () => void;
  onLoad?: () => void;
  onConfig?: () => void;
  onAutoSave?: (xml: string) => void;
  onSave?: (xml: string) => void;
  onExit?: (xml: string) => void;
  onExport?: (xml: string, fmt: Config["format"]) => void;
};

export type InitMsg = { event: "init" | "load" | "configure" };
export type SaveMsg = { event: "autosave" | "save" | "exit"; xml: string; exit?: boolean };
export type ExportMsg = { event: "export"; data: string; format: Config["format"] };
export type EditorMsg = InitMsg | SaveMsg | ExportMsg;
