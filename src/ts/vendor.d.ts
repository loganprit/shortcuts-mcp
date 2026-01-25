import type { Buffer } from "node:buffer";

declare module "plist" {
  export function parse(value: string): unknown;
  export function build(value: unknown): string;
}

declare module "bplist-parser" {
  export function parseBuffer(buffer: Buffer): unknown[];
}
