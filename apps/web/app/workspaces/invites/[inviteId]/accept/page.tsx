import { InviteAcceptClient } from "./invite-accept-client";

export default async function InviteAcceptPage({ params }: { params: Promise<{ inviteId: string }> }) {
  const { inviteId } = await params;
  return <InviteAcceptClient inviteId={inviteId} />;
}
