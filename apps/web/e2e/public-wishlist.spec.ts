import { expect, test } from "@playwright/test";

const wishlistPath = "f4c987f0-d3da-4b9f-984d-beca9b2b5260";

test("public wishlist loads and reserve updates UI", async ({ page }) => {
  let reservedByMe = false;

  await page.route("**/api/public/w/*", async route => {
    const response = {
      id: 1,
      public_id: wishlistPath,
      title: "Birthday Wishlist",
      description: null,
      currency: "USD",
      is_public: true,
      is_owner: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      items: [
        {
          id: 101,
          name: "Test Gift",
          url: null,
          image_url: null,
          price_cents: 9900,
          allow_contributions: false,
          notes: null,
          position: 0,
          is_archived: false,
          reserved: reservedByMe,
          reserved_by_me: reservedByMe,
          reserved_at: reservedByMe ? new Date().toISOString() : null,
          collected_cents: 0,
          my_contribution_cents: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ]
    };

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(response)
    });
  });

  await page.route("**/api/public/items/101/reserve", async route => {
    reservedByMe = true;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ reserved: true, reserved_at: new Date().toISOString() })
    });
  });

  await page.route("**/api/public/items/101/unreserve", async route => {
    reservedByMe = false;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ reserved: false })
    });
  });

  await page.goto(`/w/${wishlistPath}`);
  await expect(page.getByText("Test Gift")).toBeVisible();

  await page.getByRole("button", { name: "Reserve" }).click();
  await expect(page.getByText("Reserved by you")).toBeVisible();
  await expect(page.getByRole("button", { name: "Unreserve" })).toBeVisible();

  await page.getByRole("button", { name: "Unreserve" }).click();
  await expect(page.getByRole("button", { name: "Reserve" })).toBeVisible();
});
