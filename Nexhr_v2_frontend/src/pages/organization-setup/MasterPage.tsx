import { MasterManager } from '../../components/masters/MasterManager';
import { MASTER_CONFIGS, type MasterKey } from '../../masters/masterConfig';

type MasterPageProps = {
  masterKey: MasterKey;
};

export function MasterPage({ masterKey }: MasterPageProps) {
  return <MasterManager config={MASTER_CONFIGS[masterKey]} />;
}
