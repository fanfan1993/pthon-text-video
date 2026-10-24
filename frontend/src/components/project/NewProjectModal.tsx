import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Field, Input, Select, Textarea } from "@/components/ui/Input";
import { useProjectsStore } from "@/store/useProjectsStore";

const schema = z.object({
  title: z.string().max(120).optional().default("未命名项目"),
  raw_input: z.string().min(1, "请粘贴一段小说或图文文案").max(8000, "文本过长（≤8000 字）"),
  style_preset: z.enum(["anime", "realistic", "cinematic"]).default("anime"),
  aspect_ratio: z.enum(["16:9", "9:16"]).default("16:9"),
  target_duration: z.coerce.number().min(5).max(120).default(15),
});

type FormValues = z.infer<typeof schema>;

export function NewProjectModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const create = useProjectsStore((s) => s.create);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "未命名项目",
      raw_input: "",
      style_preset: "anime",
      aspect_ratio: "16:9",
      target_duration: 15,
    },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const project = await create({
        title: values.title || "未命名项目",
        raw_input: values.raw_input,
        style_preset: values.style_preset,
        aspect_ratio: values.aspect_ratio,
        target_duration: Number(values.target_duration),
      });
      reset();
      onClose();
      navigate(`/projects/${project.id}`);
    } catch (e) {
      // 提交失败保留输入，仅通过错误态提示
      console.error(e);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="新建图文 / 小说转视频项目"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            取消
          </Button>
          <Button loading={isSubmitting} onClick={handleSubmit(onSubmit)}>
            创建并进入
          </Button>
        </>
      }
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <Field label="项目标题" error={errors.title?.message}>
          <Input placeholder="例如：雨夜少女的独白" {...register("title")} />
        </Field>

        <Field
          label="小说 / 图文文案"
          hint="粘贴一段文字，作为分镜与对白的素材来源"
          error={errors.raw_input?.message}
        >
          <Textarea
            placeholder="雨夜，少女撑伞而立。路灯把她的影子拉得很长……"
            {...register("raw_input")}
          />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="风格" error={errors.style_preset?.message}>
            <Select {...register("style_preset")}>
              <option value="anime">二次元 / 动态漫</option>
              <option value="realistic">写实短剧</option>
              <option value="cinematic">电影感</option>
            </Select>
          </Field>
          <Field label="画幅" error={errors.aspect_ratio?.message}>
            <Select {...register("aspect_ratio")}>
              <option value="16:9">横屏 16:9</option>
              <option value="9:16">竖屏 9:16</option>
            </Select>
          </Field>
        </div>

        <Field label="目标时长（秒）" error={errors.target_duration?.message}>
          <Select {...register("target_duration")}>
            <option value={15}>15 秒（单镜，推荐起步）</option>
            <option value={30}>30 秒</option>
            <option value={60}>60 秒（多镜拼接）</option>
          </Select>
        </Field>
      </form>
    </Modal>
  );
}
