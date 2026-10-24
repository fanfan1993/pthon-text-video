import { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Field, Select } from "@/components/ui/Input";
import { CAMERA_OPTIONS, PROVIDER_OPTIONS } from "@/lib/constants";
import type { CameraMovement, GenerateRequest } from "@/types";

export function GenerateDialog({
  open,
  onClose,
  onConfirm,
  busy,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (opts: GenerateRequest) => void;
  busy: boolean;
}) {
  const [provider, setProvider] = useState("mock");
  const [camera, setCamera] = useState<CameraMovement>("ken_burns");
  const [doI2v, setDoI2v] = useState(false);

  const confirm = () => {
    onConfirm({
      provider: provider === "mock" ? null : provider,
      camera,
      do_i2v: doI2v,
    });
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="生成视频"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            取消
          </Button>
          <Button loading={busy} onClick={confirm}>
            开始生成
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Field label="出图 Provider" hint="默认 Mock 无需 Key；配置即梦/可灵/火山后可选">
          <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
            {PROVIDER_OPTIONS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="镜头运动方式">
          <Select value={camera} onChange={(e) => setCamera(e.target.value as CameraMovement)}>
            {CAMERA_OPTIONS.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </Select>
        </Field>

        <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <input
            type="checkbox"
            checked={doI2v}
            onChange={(e) => setDoI2v(e.target.checked)}
            className="mt-0.5 h-4 w-4 accent-accent"
          />
          <span className="text-sm">
            <span className="font-medium text-slate-200">图生视频（I2V）</span>
            <span className="mt-0.5 block text-xs text-slate-500">
              开启后用视频模型让角色动起来（消耗视频额度）；关闭则仅用 FFmpeg 镜头运
              动，边际成本≈0。
            </span>
          </span>
        </label>
      </div>
    </Modal>
  );
}
