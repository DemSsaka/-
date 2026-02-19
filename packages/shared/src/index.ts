import { z } from "zod";

export const currencySchema = z.enum(["USD", "EUR", "GBP"]);

export const wsEventSchema = z.object({
  event_id: z.string(),
  type: z.string(),
  wishlist_public_id: z.string(),
  server_ts: z.string(),
  data: z.record(z.any())
});

export type WsEvent = z.infer<typeof wsEventSchema>;
